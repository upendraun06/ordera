"""
Gmail OAuth2 Router
===================
Admin endpoints that drive the "Connect Gmail" flow shown in Settings → Email tab.

Flow
----
1. GET  /api/gmail/authorize  — Frontend calls this to get the Google consent URL
2. (browser) User authorizes at Google
3. GET  /api/gmail/callback   — Google redirects here with ?code=...
4. Backend exchanges code → stores tokens → redirects to /settings?gmail=connected
5. GET  /api/gmail/status     — Frontend polls this to show connection state
6. POST /api/gmail/test       — Send a test email to verify everything works
7. DEL  /api/gmail/disconnect — Remove stored tokens

OAuth2 requirement
------------------
The redirect URI  http://localhost:8002/api/gmail/callback  must be registered
in Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client IDs.
In production, replace with your actual domain.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from app.config import settings
from app.middleware.auth import get_current_owner
from app.models.owner import Owner
import app.services.gmail_oauth_service as gmail_svc

router = APIRouter(prefix='/api/gmail', tags=['gmail'])

# Note: authorize uses urllib directly (no oauthlib, no PKCE).
#       callback uses requests.post directly to Google's token endpoint.
#       This avoids all InsecureTransportError / PKCE verifier issues.


# ── Helpers ───────────────────────────────────────────────────────────────────

def _client_config() -> dict:
    """Build the OAuth2 client config dict from settings."""
    return {
        'web': {
            'client_id': settings.GMAIL_CLIENT_ID,
            'client_secret': settings.GMAIL_CLIENT_SECRET,
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'redirect_uris': [f'{settings.BASE_URL}/api/gmail/callback'],
        }
    }


def _redirect_uri() -> str:
    return f'{settings.BASE_URL}/api/gmail/callback'


def _require_credentials():
    """Raise 503 if Gmail OAuth2 credentials are not configured in .env."""
    if not settings.GMAIL_CLIENT_ID or not settings.GMAIL_CLIENT_SECRET:
        raise HTTPException(
            status_code=503,
            detail=(
                'Gmail OAuth2 is not configured. '
                'Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in backend/.env'
            ),
        )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get('/status')
def gmail_status(current_owner: Owner = Depends(get_current_owner)):
    """
    Return the current Gmail connection state.
    Response: { connected: bool, email?: str }
    """
    return gmail_svc.get_status()


@router.get('/authorize')
def gmail_authorize(current_owner: Owner = Depends(get_current_owner)):
    """
    Build a Google OAuth2 authorization URL and return it to the frontend.
    Uses urllib directly — no oauthlib, no PKCE, no transport quirks.
    Response: { url: str }
    """
    _require_credentials()
    from urllib.parse import urlencode

    params = {
        'client_id':     settings.GMAIL_CLIENT_ID,
        'redirect_uri':  _redirect_uri(),
        'response_type': 'code',
        'scope':         ' '.join(gmail_svc.SCOPES),
        'access_type':   'offline',   # ask Google for a refresh_token
        'prompt':        'consent',   # always return refresh_token even if previously granted
    }
    auth_url = 'https://accounts.google.com/o/oauth2/auth?' + urlencode(params)
    print(f'[Gmail OAuth] Auth URL built — redirect_uri={_redirect_uri()}')
    return {'url': auth_url}


@router.get('/callback')
def gmail_callback(code: str = None, state: str = None, error: str = None):
    """
    OAuth2 redirect endpoint — Google sends the user here after authorization.
    Exchanges the code via a direct HTTPS POST to Google (no oauthlib flow),
    fetches the sender Gmail address, saves tokens, redirects to /settings.
    """
    if error or not code:
        print(f'[Gmail OAuth] Denied / error param: {error}')
        return RedirectResponse(f'{settings.FRONTEND_URL}/settings?gmail=denied')

    try:
        import requests as http

        # ── Step 1: Exchange authorization code for tokens ────────────────────
        print(f'[Gmail OAuth] Exchanging code for tokens...')
        token_resp = http.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code':          code,
                'client_id':     settings.GMAIL_CLIENT_ID,
                'client_secret': settings.GMAIL_CLIENT_SECRET,
                'redirect_uri':  _redirect_uri(),
                'grant_type':    'authorization_code',
            },
            timeout=15,
        )
        token_data = token_resp.json()
        print(f'[Gmail OAuth] Token response keys: {list(token_data.keys())}')

        if 'error' in token_data:
            print(f'[Gmail OAuth] Token error: {token_data}')
            import urllib.parse
            msg = urllib.parse.quote(f"{token_data.get('error')}: {token_data.get('error_description','')}"[:200])
            return RedirectResponse(f'{settings.FRONTEND_URL}/settings?gmail=error&msg={msg}')

        access_token  = token_data['access_token']
        refresh_token = token_data.get('refresh_token')

        if not refresh_token:
            print('[Gmail OAuth] No refresh_token in response — user may need to re-authorize')
            return RedirectResponse(f'{settings.FRONTEND_URL}/settings?gmail=error')

        # ── Step 2: Fetch the Gmail address ───────────────────────────────────
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=settings.GMAIL_CLIENT_ID,
            client_secret=settings.GMAIL_CLIENT_SECRET,
            scopes=gmail_svc.SCOPES,
        )
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        sender_email = profile.get('emailAddress', '')

        # ── Step 3: Persist tokens ─────────────────────────────────────────────
        gmail_svc.save_credentials(creds, sender_email=sender_email)
        print(f'[Gmail OAuth] OK Connected as {sender_email}')

        return RedirectResponse(
            f'{settings.FRONTEND_URL}/settings?gmail=connected&email={sender_email}'
        )

    except Exception as e:
        import traceback, urllib.parse
        print(f'[Gmail OAuth] Callback exception: {e}')
        traceback.print_exc()
        msg = urllib.parse.quote(str(e)[:200])
        return RedirectResponse(f'{settings.FRONTEND_URL}/settings?gmail=error&msg={msg}')


@router.post('/test')
def send_test_email(current_owner: Owner = Depends(get_current_owner)):
    """
    Send a test email to the currently logged-in owner to verify the connection.
    """
    if not gmail_svc.is_configured():
        raise HTTPException(status_code=400, detail='Gmail is not connected. Connect it first in Settings → Email.')

    html = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
                max-width:480px;margin:0 auto;padding:40px 20px">
      <div style="text-align:center;margin-bottom:28px">
        <div style="width:64px;height:64px;border-radius:20px;
                    background:linear-gradient(135deg,#d1fae5,#10b981);
                    margin:0 auto 16px;display:flex;align-items:center;
                    justify-content:center;font-size:32px">✅</div>
        <h1 style="font-size:22px;font-weight:700;color:#111827;margin:0">
          Gmail Connected!
        </h1>
        <p style="font-size:14px;color:#6B7280;margin:8px 0 0">
          Your Ringa account is now sending emails via Gmail OAuth2.
        </p>
      </div>
      <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:12px;
                  padding:20px;text-align:center">
        <div style="font-size:13px;color:#166534">
          Sent successfully to <strong>{current_owner.email}</strong>
        </div>
        <div style="font-size:12px;color:#6B7280;margin-top:6px">
          All OTP codes, usage alerts, and plan notifications will now use this connection.
        </div>
      </div>
    </div>
    """
    ok = gmail_svc.send_email(
        current_owner.email,
        'Gmail OAuth2 — Connection Verified ✓',
        html,
    )
    if not ok:
        raise HTTPException(
            status_code=500,
            detail='Test email failed to send. Check the server logs for details.',
        )
    return {'sent': True, 'to': current_owner.email}


@router.delete('/disconnect')
def gmail_disconnect(current_owner: Owner = Depends(get_current_owner)):
    """Remove the stored Gmail token file (disconnect Gmail)."""
    removed = gmail_svc.remove_token()
    return {'disconnected': removed}

/**
 * printKitchenTicket(order, restaurantName)
 * Opens a thermal-style kitchen ticket in a new window and triggers print.
 */
export function printKitchenTicket(order, restaurantName = "Mario's Pizza") {
  const time = order.created_at
    ? new Date(order.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

  const printTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })

  const itemRows = (order.items || []).map(item => `
    <tr>
      <td class="qty">${item.quantity}x</td>
      <td class="name">
        ${item.name}
        ${item.modification ? `<div class="mod">→ ${item.modification}</div>` : ''}
      </td>
    </tr>
  `).join('')

  const payMethod = order.pay_method === 'stripe_link' ? 'SMS Payment Link' : 'Cash / Card at Pickup'
  const payStatus = (order.payment_status || 'pending').toUpperCase()

  const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <title>Kitchen Ticket #${order.id?.slice(0, 6).toUpperCase()}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      font-family: 'Space Mono', 'Courier New', monospace;
      font-size: 13px;
      color: #000;
      background: #fff;
      width: 80mm;
      padding: 6mm 4mm;
    }

    .center  { text-align: center; }
    .bold    { font-weight: 700; }
    .large   { font-size: 16px; }
    .xlarge  { font-size: 20px; font-weight: 700; letter-spacing: 1px; }
    .small   { font-size: 11px; }
    .muted   { color: #555; }

    .divider {
      border: none;
      border-top: 1px dashed #000;
      margin: 6px 0;
    }
    .divider-solid {
      border: none;
      border-top: 2px solid #000;
      margin: 6px 0;
    }

    .header-block  { margin-bottom: 8px; }
    .meta-row      { display: flex; justify-content: space-between; margin: 2px 0; }
    .meta-label    { color: #555; }

    table { width: 100%; border-collapse: collapse; margin: 4px 0; }
    td    { vertical-align: top; padding: 3px 0; }
    td.qty  { width: 28px; font-weight: 700; font-size: 14px; white-space: nowrap; }
    td.name { font-size: 14px; font-weight: 700; line-height: 1.4; }
    .mod    { font-size: 11px; font-weight: 400; color: #333; margin-top: 1px; }

    .special-box {
      border: 2px solid #000;
      padding: 5px 7px;
      margin: 6px 0;
      font-size: 12px;
    }
    .special-label { font-weight: 700; font-size: 11px; margin-bottom: 2px; }

    .total-row {
      display: flex;
      justify-content: space-between;
      font-size: 16px;
      font-weight: 700;
      margin: 4px 0;
    }

    .status-badge {
      display: inline-block;
      border: 2px solid #000;
      padding: 1px 6px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.5px;
    }

    .footer { margin-top: 10px; }

    @media print {
      body { padding: 2mm; }
      @page { margin: 0; size: 80mm auto; }
    }
  </style>
</head>
<body>

  <!-- Restaurant header -->
  <div class="header-block center">
    <div class="xlarge">${restaurantName.toUpperCase()}</div>
    <div class="small muted">KITCHEN ORDER TICKET</div>
  </div>

  <hr class="divider-solid"/>

  <!-- Order meta -->
  <div class="meta-row">
    <span class="bold">ORDER #</span>
    <span class="bold large">${(order.id || '').slice(0, 8).toUpperCase()}</span>
  </div>
  <div class="meta-row">
    <span class="meta-label">Time Placed</span>
    <span class="bold">${time}</span>
  </div>
  <div class="meta-row">
    <span class="meta-label">Customer</span>
    <span class="bold">${order.customer_name || 'Walk-in'}</span>
  </div>
  ${order.customer_phone ? `
  <div class="meta-row">
    <span class="meta-label">Phone</span>
    <span>${order.customer_phone}</span>
  </div>` : ''}

  <hr class="divider"/>

  <!-- Items -->
  <div class="bold small" style="margin-bottom:4px;">ITEMS</div>
  <table>
    ${itemRows}
  </table>

  <hr class="divider"/>

  <!-- Special instructions -->
  ${order.special_instructions ? `
  <div class="special-box">
    <div class="special-label">*** SPECIAL INSTRUCTIONS ***</div>
    ${order.special_instructions}
  </div>` : ''}

  <!-- Total & payment -->
  <div class="total-row">
    <span>TOTAL</span>
    <span>$${(order.total || 0).toFixed(2)}</span>
  </div>
  <div class="meta-row small">
    <span class="meta-label">${payMethod}</span>
    <span class="status-badge">${payStatus}</span>
  </div>

  <hr class="divider-solid"/>

  <!-- Footer -->
  <div class="footer center small muted">
    <div>Printed: ${printTime}</div>
    <div style="margin-top:4px;">*** END OF TICKET ***</div>
  </div>

</body>
</html>`

  const win = window.open('', '_blank', 'width=340,height=600,scrollbars=yes')
  if (!win) {
    alert('Pop-up blocked. Please allow pop-ups for this site to print tickets.')
    return
  }
  win.document.write(html)
  win.document.close()
  win.focus()
  // Small delay to let fonts load
  setTimeout(() => {
    win.print()
    setTimeout(() => win.close(), 500)
  }, 600)
}

import { useState, useEffect, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import Layout from '../components/Layout'
import { knowledgeApi } from '../services/api'

const DOC_TYPES = ['menu', 'allergy', 'policy', 'faq', 'general']
const DOC_TYPE_LABELS = {
  menu: '🍔 Menu',
  allergy: '⚠️ Allergy',
  policy: '📋 Policy',
  faq: '❓ FAQ',
  general: '📄 General',
}

export default function DocumentUpload() {
  const [documents, setDocuments] = useState([])
  const [docType, setDocType] = useState('general')
  const [uploading, setUploading] = useState(false)
  const [uploadFile, setUploadFile] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [message, setMessage] = useState('')

  const loadDocuments = async () => {
    const res = await knowledgeApi.listDocuments()
    setDocuments(res.data)
  }

  useEffect(() => { loadDocuments() }, [])

  const onDrop = useCallback((accepted) => {
    if (accepted.length > 0) setUploadFile(accepted[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxSize: 10 * 1024 * 1024,
    multiple: false,
  })

  const handleUpload = async () => {
    if (!uploadFile) return
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', uploadFile)
      formData.append('doc_type', docType)
      await knowledgeApi.upload(formData)
      setUploadFile(null)
      setMessage('Document uploaded and chunked successfully!')
      await loadDocuments()
    } catch (err) {
      setMessage('Upload failed: ' + (err.response?.data?.detail || 'Unknown error'))
    } finally {
      setUploading(false)
      setTimeout(() => setMessage(''), 4000)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this document and all its chunks?')) return
    await knowledgeApi.deleteDocument(id)
    await loadDocuments()
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    const res = await knowledgeApi.search(searchQuery)
    setSearchResults(res.data)
  }

  return (
    <Layout>
      <div className="p-6 max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-2">Knowledge Base</h1>
        <p className="text-gray-500 text-sm mb-6">
          Upload menus, allergy info, and policies. The AI uses these to answer customer questions accurately.
        </p>

        {message && (
          <div className="mb-4 bg-blue-50 text-blue-700 rounded-lg px-4 py-2 text-sm">{message}</div>
        )}

        {/* Upload Area */}
        <div className="card mb-8">
          <h2 className="font-semibold mb-4">Upload Document</h2>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Document Type</label>
            <div className="flex gap-2 flex-wrap">
              {DOC_TYPES.map(type => (
                <button
                  key={type}
                  onClick={() => setDocType(type)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    docType === type ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {DOC_TYPE_LABELS[type]}
                </button>
              ))}
            </div>
          </div>

          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
              isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
            }`}
          >
            <input {...getInputProps()} />
            {uploadFile ? (
              <div>
                <div className="text-3xl mb-2">📄</div>
                <div className="font-medium">{uploadFile.name}</div>
                <div className="text-sm text-gray-500">{(uploadFile.size / 1024).toFixed(1)} KB</div>
              </div>
            ) : (
              <div>
                <div className="text-4xl mb-2">☁️</div>
                <div className="font-medium text-gray-700">
                  {isDragActive ? 'Drop here!' : 'Drag & drop or click to upload'}
                </div>
                <div className="text-sm text-gray-400 mt-1">PDF, DOCX, TXT • Max 10MB</div>
              </div>
            )}
          </div>

          {uploadFile && (
            <div className="mt-4 flex gap-2">
              <button onClick={handleUpload} disabled={uploading} className="btn-primary">
                {uploading ? 'Processing...' : `Upload as ${DOC_TYPE_LABELS[docType]}`}
              </button>
              <button onClick={() => setUploadFile(null)} className="btn-secondary">Cancel</button>
            </div>
          )}
        </div>

        {/* Uploaded Documents */}
        <div className="card mb-8">
          <h2 className="font-semibold mb-4">Uploaded Documents ({documents.length})</h2>
          {documents.length === 0 ? (
            <div className="text-center py-6 text-gray-400">No documents yet. Upload your menu to get started!</div>
          ) : (
            <div className="space-y-3">
              {documents.map(doc => (
                <div key={doc.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 border">
                  <div>
                    <div className="font-medium">{doc.filename}</div>
                    <div className="text-xs text-gray-500">
                      {DOC_TYPE_LABELS[doc.doc_type]} • {doc.chunk_count} chunks •{' '}
                      {new Date(doc.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <button onClick={() => handleDelete(doc.id)} className="text-red-500 text-sm hover:underline">
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* RAG Search Test */}
        <div className="card">
          <h2 className="font-semibold mb-4">Test Knowledge Search</h2>
          <form onSubmit={handleSearch} className="flex gap-2 mb-4">
            <input
              className="input"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="e.g. 'is the burger gluten free?' or 'delivery policy'"
            />
            <button type="submit" className="btn-primary whitespace-nowrap">Search</button>
          </form>
          {searchResults.length > 0 && (
            <div className="space-y-3">
              {searchResults.map((result, i) => (
                <div key={i} className="p-3 rounded-lg border bg-gray-50">
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>{DOC_TYPE_LABELS[result.doc_type] || result.doc_type}</span>
                    <span>Score: {(result.score * 100).toFixed(0)}%</span>
                  </div>
                  <p className="text-sm text-gray-800">{result.chunk_text}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}

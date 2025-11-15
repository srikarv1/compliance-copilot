'use client'

import { useState } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { DocumentArrowUpIcon } from '@heroicons/react/24/outline'

export default function DocumentUpload() {
  const [uploading, setUploading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([])

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (file.type !== 'application/pdf') {
      toast.error('Please upload a PDF file')
      return
    }

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/documents/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )
      setUploadedFiles([...uploadedFiles, file.name])
      toast.success(`Document "${file.name}" uploaded successfully!`)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
        <DocumentArrowUpIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <label className="cursor-pointer">
          <span className="text-blue-600 hover:text-blue-700 font-medium">
            {uploading ? 'Uploading...' : 'Click to upload PDF'}
          </span>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileUpload}
            disabled={uploading}
            className="hidden"
          />
        </label>
        <p className="text-sm text-gray-500 mt-2">
          Upload regulatory documents, policies, or audit logs
        </p>
      </div>

      {uploadedFiles.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Uploaded Files:</h3>
          <ul className="space-y-1">
            {uploadedFiles.map((filename, index) => (
              <li key={index} className="text-sm text-gray-600 flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                {filename}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}


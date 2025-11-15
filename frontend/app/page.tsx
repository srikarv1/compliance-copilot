'use client'

import { useState } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import DocumentUpload from '@/components/DocumentUpload'
import ComplianceAnalyzer from '@/components/ComplianceAnalyzer'
import ResultsDisplay from '@/components/ResultsDisplay'

interface ComplianceResult {
  final_report: string
  risk_assessment: string
  extracted_policies: string
  verification: string
  agent_history: string[]
}

export default function Home() {
  const [results, setResults] = useState<ComplianceResult | null>(null)
  const [loading, setLoading] = useState(false)

  const handleAnalysis = async (query: string, transactionData: any) => {
    setLoading(true)
    try {
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/compliance/analyze`,
        {
          query,
          transaction_data: transactionData,
        }
      )
      setResults(response.data)
      toast.success('Analysis completed successfully!')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Analysis failed')
      console.error('Analysis error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-5xl font-bold text-gray-900 mb-2">
            Compliance Copilot
          </h1>
          <p className="text-xl text-gray-600">
            AI-Powered Banking Compliance Analysis System
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Powered by LangChain, LangGraph, and Multi-Agent Architecture
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-semibold mb-4">Upload Documents</h2>
            <DocumentUpload />
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-semibold mb-4">Compliance Analysis</h2>
            <ComplianceAnalyzer onAnalyze={handleAnalysis} loading={loading} />
          </div>
        </div>

        {results && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <ResultsDisplay results={results} />
          </div>
        )}
      </div>
    </main>
  )
}


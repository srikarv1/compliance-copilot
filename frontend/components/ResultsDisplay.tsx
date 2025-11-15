'use client'

import { useState } from 'react'
import { DocumentTextIcon, ShieldCheckIcon, ExclamationTriangleIcon, CheckCircleIcon } from '@heroicons/react/24/outline'

interface ComplianceResult {
  final_report: string
  risk_assessment: string
  extracted_policies: string
  verification: string
  agent_history: string[]
}

interface ResultsDisplayProps {
  results: ComplianceResult
}

export default function ResultsDisplay({ results }: ResultsDisplayProps) {
  const [activeTab, setActiveTab] = useState<'report' | 'risk' | 'policies' | 'verification'>('report')

  const tabs = [
    { id: 'report', name: 'Final Report', icon: DocumentTextIcon },
    { id: 'risk', name: 'Risk Assessment', icon: ShieldCheckIcon },
    { id: 'policies', name: 'Policies', icon: DocumentTextIcon },
    { id: 'verification', name: 'Verification', icon: CheckCircleIcon },
  ]

  const renderContent = () => {
    switch (activeTab) {
      case 'report':
        return (
          <div className="prose max-w-none">
            <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-4 rounded-lg">
              {results.final_report}
            </pre>
          </div>
        )
      case 'risk':
        return (
          <div className="prose max-w-none">
            <pre className="whitespace-pre-wrap text-sm bg-red-50 p-4 rounded-lg">
              {results.risk_assessment}
            </pre>
          </div>
        )
      case 'policies':
        return (
          <div className="prose max-w-none">
            <pre className="whitespace-pre-wrap text-sm bg-blue-50 p-4 rounded-lg">
              {results.extracted_policies}
            </pre>
          </div>
        )
      case 'verification':
        return (
          <div className="prose max-w-none">
            <pre className="whitespace-pre-wrap text-sm bg-green-50 p-4 rounded-lg">
              {results.verification}
            </pre>
          </div>
        )
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">Analysis Results</h2>

      {/* Agent History */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Agent Execution History</h3>
        <div className="space-y-1">
          {results.agent_history.map((step, index) => (
            <div key={index} className="text-sm text-gray-600 flex items-center">
              <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
              {step}
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-4">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`
                  flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm
                  ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <Icon className="h-5 w-5" />
                {tab.name}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Content */}
      <div className="mt-4">{renderContent()}</div>
    </div>
  )
}


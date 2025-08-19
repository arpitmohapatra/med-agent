import React from 'react';
import { DocumentTextIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { Source } from '../../types';
import SourceCard from './SourceCard';
import { classNames } from '../../utils/helpers';

interface SourcePanelProps {
  sources: Source[];
  isLoading?: boolean;
  query?: string;
}

const SourcePanel: React.FC<SourcePanelProps> = ({
  sources,
  isLoading = false,
  query,
}) => {
  if (isLoading) {
    return (
      <div className="bg-gray-50 border-l border-gray-200 w-80 p-4">
        <div className="flex items-center space-x-2 mb-4">
          <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 animate-pulse" />
          <h2 className="text-lg font-medium text-gray-900">Searching...</h2>
        </div>
        
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex items-center space-x-2 mb-3">
                  <div className="w-6 h-6 bg-gray-200 rounded-full"></div>
                  <div className="h-4 bg-gray-200 rounded flex-1"></div>
                </div>
                <div className="space-y-2">
                  <div className="h-3 bg-gray-200 rounded"></div>
                  <div className="h-3 bg-gray-200 rounded w-3/4"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!sources || sources.length === 0) {
    return (
      <div className="bg-gray-50 border-l border-gray-200 w-80 p-4">
        <div className="flex items-center space-x-2 mb-4">
          <DocumentTextIcon className="w-5 h-5 text-gray-400" />
          <h2 className="text-lg font-medium text-gray-900">Sources</h2>
        </div>
        
        <div className="text-center py-8">
          <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-300" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No sources</h3>
          <p className="mt-1 text-sm text-gray-500">
            Sources will appear here when using RAG mode
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-50 border-l border-gray-200 w-80 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center space-x-2 mb-2">
          <DocumentTextIcon className="w-5 h-5 text-medical-600" />
          <h2 className="text-lg font-medium text-gray-900">Sources</h2>
          <span className="bg-medical-100 text-medical-800 text-xs px-2 py-1 rounded-full">
            {sources.length}
          </span>
        </div>
        
        {query && (
          <p className="text-sm text-gray-600">
            Results for: <span className="font-medium">"{query}"</span>
          </p>
        )}
      </div>

      {/* Sources List */}
      <div className="flex-1 p-4 space-y-4 overflow-y-auto custom-scrollbar">
        {sources.map((source, index) => (
          <SourceCard
            key={source.id}
            source={source}
            index={index}
          />
        ))}
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-gray-200 bg-white">
        <div className="text-xs text-gray-500 space-y-1">
          <p>📊 Sources ranked by relevance</p>
          <p>🔗 Click "View" to open full content</p>
          <p>⚕️ Information is for educational purposes</p>
        </div>
      </div>
    </div>
  );
};

export default SourcePanel;

import React from 'react';
import { 
  Link2, 
  Star, 
  FileText,
  Info,
  AlertTriangle,
  ArrowLeftRight
} from 'lucide-react';
import { Source } from '../../types';
import { extractMedicineInfo, truncateText, classNames } from '../../utils/helpers';

interface SourceCardProps {
  source: Source;
  index: number;
}

const SourceCard: React.FC<SourceCardProps> = ({ source, index }) => {
  const medicineInfo = extractMedicineInfo(source.metadata);
  
  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const handleCardClick = () => {
    if (source.url) {
      window.open(source.url, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <div className="source-card bg-white rounded-lg border border-gray-200 p-4 hover:shadow-lg transition-all duration-200">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-xs font-medium">
            {index + 1}
          </div>
          <h3 className="font-medium text-gray-900 text-sm line-clamp-2">
            {source.title}
          </h3>
        </div>
        
        <div className={classNames(
          'text-xs px-2 py-1 rounded-full font-medium',
          getScoreColor(source.score)
        )}>
          <Star className="w-3 h-3 inline mr-1" />
          {(source.score * 100).toFixed(0)}%
        </div>
      </div>

      {/* Medicine Information */}
      {medicineInfo.name && medicineInfo.name !== 'Unknown Medicine' && (
        <div className="mb-3 space-y-2">
          {/* Chemical/Therapeutic Class */}
          {(medicineInfo.chemicalClass || medicineInfo.therapeuticClass) && (
            <div className="flex items-start space-x-2">
              <FileText className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-xs font-medium text-gray-600">Class:</span>
                <p className="text-sm text-gray-700">
                  {[medicineInfo.chemicalClass, medicineInfo.therapeuticClass]
                    .filter(c => c && c !== 'NA')
                    .join(' • ')
                  }
                </p>
              </div>
            </div>
          )}
          
          {medicineInfo.uses && (
            <div className="flex items-start space-x-2">
              <Info className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-xs font-medium text-gray-600">Uses:</span>
                <p className="text-sm text-gray-700">{truncateText(medicineInfo.uses, 120)}</p>
              </div>
            </div>
          )}
          
          {medicineInfo.sideEffects && (
            <div className="flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-xs font-medium text-gray-600">Side Effects:</span>
                <p className="text-sm text-gray-700">{truncateText(medicineInfo.sideEffects, 120)}</p>
              </div>
            </div>
          )}
          
          {medicineInfo.substitutes && (
            <div className="flex items-start space-x-2">
              <ArrowLeftRight className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-xs font-medium text-gray-600">Substitutes:</span>
                <p className="text-sm text-gray-700">{truncateText(medicineInfo.substitutes, 120)}</p>
              </div>
            </div>
          )}
          
          {/* Habit Forming Warning */}
          {medicineInfo.habitForming && medicineInfo.habitForming !== 'No' && medicineInfo.habitForming !== 'NA' && (
            <div className="flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-xs font-medium text-red-600">Habit Forming:</span>
                <p className="text-sm text-red-700">{medicineInfo.habitForming}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Content Preview */}
      <div className="mb-3">
        <p className="text-sm text-gray-600 line-clamp-3">
          {truncateText(source.content, 150)}
        </p>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center space-x-3">
          {medicineInfo.actionClass && medicineInfo.actionClass !== 'NA' && (
            <span>{medicineInfo.actionClass}</span>
          )}
          {medicineInfo.medicineId && (
            <span>ID: {medicineInfo.medicineId}</span>
          )}
          {source.metadata.type && (
            <span className="capitalize">{source.metadata.type}</span>
          )}
        </div>
        
        {source.url && (
          <button
            onClick={handleCardClick}
            className="flex items-center space-x-1 text-primary-600 hover:text-primary-700 transition-colors"
          >
            <Link2 className="w-3 h-3" />
            <span>View</span>
          </button>
        )}
      </div>
    </div>
  );
};

export default SourceCard;

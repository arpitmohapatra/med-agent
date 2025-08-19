import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Cog6ToothIcon, 
  UserCircleIcon,
  ChatBubbleLeftRightIcon,
  DocumentMagnifyingGlassIcon,
  CpuChipIcon 
} from '@heroicons/react/24/outline';
import { ChatMode } from '../../types';
import { CHAT_MODE_LABELS, CHAT_MODE_DESCRIPTIONS } from '../../utils/constants';
import { classNames } from '../../utils/helpers';

interface HeaderProps {
  currentMode: ChatMode;
  onModeChange: (mode: ChatMode) => void;
  onSettingsClick: () => void;
  onLogout: () => void;
  currentUser?: any;
}

const Header: React.FC<HeaderProps> = ({
  currentMode,
  onModeChange,
  onSettingsClick,
  onLogout,
  currentUser,
}) => {
  const navigate = useNavigate();

  const modes: Array<{ key: ChatMode; icon: React.ElementType; color: string }> = [
    { key: 'ask', icon: ChatBubbleLeftRightIcon, color: 'text-blue-600' },
    { key: 'rag', icon: DocumentMagnifyingGlassIcon, color: 'text-medical-600' },
    { key: 'agent', icon: CpuChipIcon, color: 'text-purple-600' },
  ];

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Logo and Title */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-medical-500 to-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">M</span>
            </div>
            <h1 className="text-xl font-semibold text-gray-900">MedQuery</h1>
          </div>
        </div>

        {/* Mode Switcher */}
        <div className="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
          {modes.map(({ key, icon: Icon, color }) => (
            <button
              key={key}
              onClick={() => onModeChange(key)}
              className={classNames(
                'flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200',
                currentMode === key
                  ? 'bg-white shadow-sm text-gray-900'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-white/50'
              )}
              title={CHAT_MODE_DESCRIPTIONS[key]}
            >
              <Icon 
                className={classNames(
                  'w-4 h-4',
                  currentMode === key ? color : 'text-gray-400'
                )} 
              />
              <span>{CHAT_MODE_LABELS[key]}</span>
            </button>
          ))}
        </div>

        {/* User Menu */}
        <div className="flex items-center space-x-4">
          <button
            onClick={onSettingsClick}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            title="Settings"
          >
            <Cog6ToothIcon className="w-5 h-5" />
          </button>
          
          <div className="flex items-center space-x-2">
            <UserCircleIcon className="w-6 h-6 text-gray-400" />
            <span className="text-sm text-gray-700">
              {currentUser?.full_name || currentUser?.username || 'User'}
            </span>
            <button
              onClick={onLogout}
              className="text-sm text-gray-500 hover:text-gray-700 ml-2"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Mode Description */}
      <div className="mt-2 text-sm text-gray-500">
        {CHAT_MODE_DESCRIPTIONS[currentMode]}
      </div>
    </header>
  );
};

export default Header;

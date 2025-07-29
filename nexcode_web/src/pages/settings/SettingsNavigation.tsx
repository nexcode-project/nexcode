import { User, Key, Building2 } from 'lucide-react';

interface SettingsNavigationProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export default function SettingsNavigation({ activeTab, onTabChange }: SettingsNavigationProps) {
  return (
    <div className="w-64 flex-shrink-0">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <nav className="space-y-2">
          <button
            onClick={() => onTabChange('profile')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-left transition-colors ${
              activeTab === 'profile'
                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
            }`}
          >
            <User className={`w-5 h-5 ${activeTab === 'profile' ? 'text-blue-600' : 'text-gray-400'}`} />
            <span className="font-medium">Profile</span>
          </button>
          <button
            onClick={() => onTabChange('tokens')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-left transition-colors ${
              activeTab === 'tokens'
                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
            }`}
          >
            <Key className={`w-5 h-5 ${activeTab === 'tokens' ? 'text-blue-600' : 'text-gray-400'}`} />
            <span className="font-medium">Personal Access Tokens</span>
          </button>
          <button
            onClick={() => onTabChange('organizations')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-left transition-colors ${
              activeTab === 'organizations'
                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
            }`}
          >
            <Building2 className={`w-5 h-5 ${activeTab === 'organizations' ? 'text-blue-600' : 'text-gray-400'}`} />
            <span className="font-medium">Organizations</span>
          </button>
        </nav>
      </div>
    </div>
  );
} 
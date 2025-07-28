import { User, Shield } from 'lucide-react';
import type { User as UserType } from '@/types/api';

interface ProfileTabProps {
  user: UserType | null;
}

export default function ProfileTab({ user }: ProfileTabProps) {
  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-6">
        <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full flex items-center justify-center">
          <User className="w-10 h-10 text-blue-600" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            {user?.username}
          </h2>
          <p className="text-lg text-gray-500">{user?.email}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-4">
          <label className="block text-lg font-medium text-gray-700">
            用户名
          </label>
          <input
            type="text"
            value={user?.username || ''}
            disabled
            className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-50 text-gray-500 text-lg"
          />
        </div>
        <div className="space-y-4">
          <label className="block text-lg font-medium text-gray-700">
            邮箱
          </label>
          <input
            type="email"
            value={user?.email || ''}
            disabled
            className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-50 text-gray-500 text-lg"
          />
        </div>
      </div>

      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6">
        <div className="flex items-start space-x-4">
          <Shield className="w-6 h-6 text-blue-600 mt-1" />
          <div>
            <h4 className="text-lg font-semibold text-blue-900 mb-2">
              账户安全提示
            </h4>
            <p className="text-blue-700 leading-relaxed">
              如需修改密码或更新个人信息，请联系系统管理员。我们致力于保护您的账户安全。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
} 
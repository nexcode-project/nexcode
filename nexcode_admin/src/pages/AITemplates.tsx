import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Save, X } from 'lucide-react';
import { aiTemplatesAPI } from '../services/api';
import type { AITemplate, AITemplateCreate, AITemplateUpdate } from '../services/api';

interface TemplateFormData {
  name: string;
  description: string;
  system_prompt: string;
  user_prompt: string;
  category: string;
}

export default function AITemplates() {
  const [templates, setTemplates] = useState<AITemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<AITemplate | null>(null);
  const [formData, setFormData] = useState<TemplateFormData>({
    name: '',
    description: '',
    system_prompt: '',
    user_prompt: '',
    category: ''
  });

  // 预设分类
  const categories = [
    '用户故事',
    '需求分析',
    '技术文档',
    '测试用例',
    '代码评审',
    '项目管理',
    '其他'
  ];

  // 预设模板
  const presetTemplates = [
    {
      name: '用户故事生成',
      description: '根据功能需求生成标准用户故事',
      category: '用户故事',
      system_prompt: '你是一个产品经理专家，擅长编写清晰、具体的用户故事。请根据用户提供的功能需求，生成符合INVEST原则的用户故事。格式应包含：作为[角色]，我希望[功能]，以便[价值]。同时提供验收标准。',
      user_prompt: '请为以下功能需求生成用户故事：\n\n{document}\n\n请包含：\n1. 用户故事描述\n2. 验收标准\n3. 优先级建议'
    },
    {
      name: '需求分析',
      description: '对文档内容进行需求分析和整理',
      category: '需求分析',
      system_prompt: '你是一个业务分析师，擅长分析和整理业务需求。请对用户提供的内容进行深入分析，识别功能需求、非功能需求、约束条件等。',
      user_prompt: '请对以下内容进行需求分析：\n\n{document}\n\n请提供：\n1. 功能需求列表\n2. 非功能需求\n3. 约束条件\n4. 风险评估\n5. 建议'
    },
    {
      name: '技术文档优化',
      description: '优化技术文档的结构和内容',
      category: '技术文档',
      system_prompt: '你是一个技术写作专家，擅长编写清晰、准确的技术文档。请帮助优化文档结构，提高可读性和准确性。',
      user_prompt: '请优化以下技术文档：\n\n{document}\n\n请改进：\n1. 文档结构\n2. 内容准确性\n3. 可读性\n4. 添加必要的示例'
    }
  ];

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setIsLoading(true);
      const templates = await aiTemplatesAPI.getAllTemplates();
      setTemplates(templates);
    } catch (error) {
      console.error('Failed to load templates:', error);
      setTemplates([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingTemplate) {
        // 更新模板
        await aiTemplatesAPI.updateTemplate(editingTemplate.id, formData);
      } else {
        // 创建新模板
        await aiTemplatesAPI.createTemplate(formData);
      }
      
      resetForm();
      loadTemplates();
    } catch (error) {
      console.error('Failed to save template:', error);
      alert('保存模板失败，请重试');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除此模板吗？')) return;
    
    try {
      await aiTemplatesAPI.deleteTemplate(id);
      loadTemplates();
    } catch (error) {
      console.error('Failed to delete template:', error);
      alert('删除模板失败，请重试');
    }
  };

  const handleEdit = (template: AITemplate) => {
    setEditingTemplate(template);
    setFormData({
      name: template.name,
      description: template.description,
      system_prompt: template.system_prompt,
      user_prompt: template.user_prompt,
      category: template.category
    });
    setShowModal(true);
  };

  const handleUsePreset = (preset: any) => {
    setFormData({
      name: preset.name,
      description: preset.description,
      system_prompt: preset.system_prompt,
      user_prompt: preset.user_prompt,
      category: preset.category
    });
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      system_prompt: '',
      user_prompt: '',
      category: ''
    });
    setEditingTemplate(null);
    setShowModal(false);
  };

  const toggleActive = async (id: number, isActive: boolean) => {
    try {
      await aiTemplatesAPI.updateTemplate(id, { is_active: isActive });
      loadTemplates();
    } catch (error) {
      console.error('Failed to toggle template status:', error);
      alert('更新模板状态失败，请重试');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI模板管理</h1>
          <p className="text-gray-600 mt-1">管理AI助手的提示模板</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          <span>添加模板</span>
        </button>
      </div>

      {/* 模板列表 */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">现有模板</h2>
        </div>
        
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">加载中...</div>
        ) : templates.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <p>暂无AI模板</p>
            <p className="text-sm mt-1">点击"添加模板"创建第一个模板</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {templates.map((template) => (
              <div key={template.id} className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-lg font-medium text-gray-900">{template.name}</h3>
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                        {template.category}
                      </span>
                      <div className="flex items-center">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={template.is_active}
                            onChange={(e) => toggleActive(template.id, e.target.checked)}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="ml-2 text-sm text-gray-600">启用</span>
                        </label>
                      </div>
                    </div>
                    <p className="text-gray-600 mt-1">{template.description}</p>
                    
                    <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 mb-2">系统提示</h4>
                        <div className="p-3 bg-gray-50 rounded text-sm text-gray-600 max-h-32 overflow-y-auto">
                          {template.system_prompt}
                        </div>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 mb-2">用户提示</h4>
                        <div className="p-3 bg-gray-50 rounded text-sm text-gray-600 max-h-32 overflow-y-auto">
                          {template.user_prompt}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => handleEdit(template)}
                      className="p-2 text-gray-400 hover:text-blue-600"
                    >
                      <Edit className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(template.id)}
                      className="p-2 text-gray-400 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 模板表单模态框 */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">
                {editingTemplate ? '编辑模板' : '添加新模板'}
              </h3>
              <button
                onClick={resetForm}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              {/* 预设模板选择 */}
              {!editingTemplate && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    快速开始（可选）
                  </label>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {presetTemplates.map((preset, index) => (
                      <button
                        key={index}
                        type="button"
                        onClick={() => handleUsePreset(preset)}
                        className="p-3 text-left border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50"
                      >
                        <div className="font-medium text-gray-900">{preset.name}</div>
                        <div className="text-sm text-gray-600">{preset.description}</div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    模板名称 *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="例如：用户故事生成"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    分类 *
                  </label>
                  <select
                    required
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">选择分类</option>
                    {categories.map((category) => (
                      <option key={category} value={category}>{category}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  描述 *
                </label>
                <input
                  type="text"
                  required
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="简短描述此模板的用途"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  系统提示 (System Prompt) *
                </label>
                <textarea
                  required
                  rows={6}
                  value={formData.system_prompt}
                  onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="定义AI的角色和行为方式..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  用户提示 (User Prompt) *
                </label>
                <textarea
                  required
                  rows={6}
                  value={formData.user_prompt}
                  onChange={(e) => setFormData({ ...formData, user_prompt: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="用户输入的模板，可使用 {document} 占位符表示文档内容..."
                />
                <p className="mt-1 text-xs text-gray-500">
                  提示：使用 {"{document}"} 作为占位符，系统会自动替换为当前文档内容
                </p>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={resetForm}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Save className="h-4 w-4" />
                  <span>{editingTemplate ? '更新' : '创建'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
} 
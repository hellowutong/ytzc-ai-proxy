/**
 * Skill 管理 API
 */

const BASE_URL = '/admin/ai/v1'

export interface FileNode {
  name: string
  type: 'file' | 'directory'
  path: string
  editable: boolean
  is_custom?: boolean
  children?: FileNode[]
}

export interface SkillFileTree {
  category: string
  is_custom: boolean
  files: FileNode[]
}

export interface FileContent {
  path: string
  content: string
  editable: boolean
  type: 'text' | 'binary'
  size?: number
}

export interface ValidationResult {
  valid: boolean
  errors: Array<{
    line: number
    column: number
    message: string
  }>
  warnings: Array<{
    line: number
    message: string
    suggestion?: string
  }>
}

/**
 * 获取 Skill 分类文件树（包含所有版本和所有 Skill）
 */
export async function getSkillFiles(
  category: string,
  isCustom: boolean = false
): Promise<SkillFileTree | null> {
  const params = new URLSearchParams({
    category,
    is_custom: String(isCustom)
  })
  
  const response = await fetch(`${BASE_URL}/skill-files?${params}`)
  const result = await response.json()
  
  if (result.code === 200) {
    return result.data
  }
  return null
}

/**
 * 读取文件内容
 * 文件路径格式：v1/default/SKILL.md（相对于 category 目录）
 */
export async function getFileContent(
  category: string,
  filePath: string,
  isCustom: boolean = false
): Promise<FileContent | null> {
  const params = new URLSearchParams({
    category,
    file_path: filePath,
    is_custom: String(isCustom)
  })
  
  const response = await fetch(`${BASE_URL}/skill-files/content?${params}`)
  const result = await response.json()
  
  if (result.code === 200) {
    return result.data
  }
  return null
}

/**
 * 保存文件内容
 */
export async function saveFileContent(data: {
  category: string
  file_path: string  // 包含版本和skill名称，如 v1/default/SKILL.md
  content: string
  is_custom: boolean
}): Promise<boolean> {
  const response = await fetch(`${BASE_URL}/skill-files/content`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  
  const result = await response.json()
  return result.code === 200
}

/**
 * 创建文件
 */
export async function createFile(data: {
  category: string
  file_name: string
  parent_path: string  // 包含版本和skill名称，如 v1/default
  is_custom: boolean
}): Promise<{ path: string } | null> {
  const response = await fetch(`${BASE_URL}/skill-files/operation?operation=create_file`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  
  const result = await response.json()
  if (result.code === 200) {
    return result.data
  }
  throw new Error(result.message)
}

/**
 * 创建文件夹
 */
export async function createFolder(data: {
  category: string
  folder_name: string
  parent_path: string  // 包含版本和skill名称，如 v1/default
  is_custom: boolean
}): Promise<{ path: string } | null> {
  const response = await fetch(`${BASE_URL}/skill-files/operation?operation=create_folder`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  
  const result = await response.json()
  if (result.code === 200) {
    return result.data
  }
  throw new Error(result.message)
}

/**
 * 重命名文件/文件夹
 */
export async function renameItem(data: {
  category: string
  old_path: string  // 完整路径，如 v1/default/old_name.md
  new_name: string
  is_custom: boolean
}): Promise<{ path: string } | null> {
  const response = await fetch(`${BASE_URL}/skill-files/operation?operation=rename`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  
  const result = await response.json()
  if (result.code === 200) {
    return result.data
  }
  throw new Error(result.message)
}

/**
 * 删除文件/文件夹
 */
export async function deleteFile(
  category: string,
  filePath: string,  // 完整路径，如 v1/default/some_file.md
  isCustom: boolean = false
): Promise<boolean> {
  const params = new URLSearchParams({
    category,
    file_path: filePath,
    is_custom: String(isCustom)
  })
  
  const response = await fetch(`${BASE_URL}/skill-files?${params}`, {
    method: 'DELETE'
  })
  
  const result = await response.json()
  return result.code === 200
}

/**
 * 校验文件内容
 */
export async function validateFile(
  filePath: string,
  content: string
): Promise<ValidationResult> {
  const response = await fetch(`${BASE_URL}/skill-files/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_path: filePath, content })
  })
  
  const result = await response.json()
  if (result.code === 200) {
    return result.data
  }
  return { valid: false, errors: [{ line: 1, column: 1, message: result.message }], warnings: [] }
}

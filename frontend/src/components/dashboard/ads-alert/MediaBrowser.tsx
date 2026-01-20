// frontend/src/components/dashboard/ads-alert/MediaBrowser.tsx
import React, { useState, useEffect, useCallback } from 'react'
import styled from 'styled-components'
import { adsAlertService } from '../../../services/adsAlertApi'
import { MediaFile, FolderTreeNode } from '../../../types/adsAlert'

interface MediaBrowserProps {
  onSelect?: (files: MediaFile[]) => void
  multiSelect?: boolean
  selectedIds?: string[]
  filterType?: 'image' | 'video' | 'document' | 'all'
}

const Container = styled.div`
  display: flex;
  height: 400px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  background: white;
`

const Sidebar = styled.div`
  width: 200px;
  border-right: 1px solid #e5e7eb;
  overflow-y: auto;
  background: #fafafa;
`

const SidebarHeader = styled.div`
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  font-weight: 600;
  font-size: 14px;
  color: #374151;
  display: flex;
  align-items: center;
  gap: 8px;
`

const FolderTree = styled.div`
  padding: 8px;
`

const FolderItem = styled.div<{ $active: boolean; $depth: number }>`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  padding-left: ${props => 12 + props.$depth * 16}px;
  cursor: pointer;
  border-radius: 6px;
  font-size: 13px;
  color: ${props => props.$active ? '#4A90E2' : '#4b5563'};
  background: ${props => props.$active ? 'rgba(74, 144, 226, 0.1)' : 'transparent'};

  &:hover {
    background: ${props => props.$active ? 'rgba(74, 144, 226, 0.1)' : '#f3f4f6'};
  }
`

const FolderIcon = styled.span`
  font-size: 14px;
`

const FolderName = styled.span`
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`

const ExpandButton = styled.button<{ $expanded: boolean }>`
  width: 16px;
  height: 16px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 10px;
  color: #9ca3af;
  transform: rotate(${props => props.$expanded ? '90deg' : '0deg'});
  transition: transform 0.2s;

  &:hover {
    color: #4b5563;
  }
`

const MainContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`

const Toolbar = styled.div`
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 12px;
`

const Breadcrumb = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  flex: 1;
`

const BreadcrumbItem = styled.span<{ $clickable?: boolean }>`
  color: ${props => props.$clickable ? '#4A90E2' : '#374151'};
  cursor: ${props => props.$clickable ? 'pointer' : 'default'};

  &:hover {
    ${props => props.$clickable && 'text-decoration: underline;'}
  }
`

const BreadcrumbSeparator = styled.span`
  color: #9ca3af;
`

const SearchInput = styled.input`
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  width: 200px;

  &:focus {
    outline: none;
    border-color: #4A90E2;
  }
`

const FileGrid = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
  align-content: start;
`

const FileItem = styled.div<{ $selected: boolean }>`
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  border-radius: 8px;
  cursor: pointer;
  border: 2px solid ${props => props.$selected ? '#4A90E2' : 'transparent'};
  background: ${props => props.$selected ? 'rgba(74, 144, 226, 0.05)' : 'transparent'};

  &:hover {
    background: ${props => props.$selected ? 'rgba(74, 144, 226, 0.1)' : '#f3f4f6'};
  }
`

const FileThumbnail = styled.div`
  width: 80px;
  height: 80px;
  border-radius: 6px;
  overflow: hidden;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
`

const ThumbnailImage = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
`

const ThumbnailIcon = styled.div`
  font-size: 32px;
`

const FileName = styled.span`
  font-size: 11px;
  color: #4b5563;
  text-align: center;
  word-break: break-word;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
`

const FileSize = styled.span`
  font-size: 10px;
  color: #9ca3af;
  margin-top: 2px;
`

const EmptyState = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  padding: 40px;
`

const EmptyIcon = styled.div`
  font-size: 48px;
  margin-bottom: 16px;
`

const EmptyText = styled.p`
  font-size: 14px;
  margin: 0;
`

const LoadingOverlay = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
`

const StatusBar = styled.div`
  padding: 8px 16px;
  border-top: 1px solid #e5e7eb;
  font-size: 12px;
  color: #6b7280;
  display: flex;
  justify-content: space-between;
`

const SelectionInfo = styled.span`
  color: #4A90E2;
  font-weight: 500;
`

interface FolderNode extends FolderTreeNode {
  expanded?: boolean
}

const MediaBrowser: React.FC<MediaBrowserProps> = ({
  onSelect,
  multiSelect = false,
  selectedIds = [],
  filterType = 'all'
}) => {
  const [folders, setFolders] = useState<FolderNode[]>([])
  const [files, setFiles] = useState<MediaFile[]>([])
  const [currentFolder, setCurrentFolder] = useState<string | null>(null)
  const [breadcrumbs, setBreadcrumbs] = useState<{ id: string | null; name: string }[]>([
    { id: null, name: 'Root' }
  ])
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set(selectedIds))
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())

  // Load folder tree
  useEffect(() => {
    const loadFolderTree = async () => {
      try {
        const tree = await adsAlertService.getFolderTree()
        setFolders(tree)
      } catch (error) {
        console.error('Failed to load folder tree:', error)
      }
    }
    loadFolderTree()
  }, [])

  // Load files when folder changes or search query changes
  useEffect(() => {
    const loadFiles = async () => {
      setLoading(true)
      try {
        let loadedFiles: MediaFile[]
        if (searchQuery) {
          loadedFiles = await adsAlertService.searchMedia(searchQuery)
        } else {
          loadedFiles = await adsAlertService.listMedia({
            folder_id: currentFolder || undefined
          })
        }

        // Apply type filter
        if (filterType !== 'all') {
          loadedFiles = loadedFiles.filter(f => {
            const type = adsAlertService.getMediaCategory(f.file_type)
            return type === filterType
          })
        }

        setFiles(loadedFiles)
      } catch (error) {
        console.error('Failed to load files:', error)
        setFiles([])
      } finally {
        setLoading(false)
      }
    }
    loadFiles()
  }, [currentFolder, searchQuery, filterType])

  // Update selected files when external selection changes
  useEffect(() => {
    setSelectedFiles(new Set(selectedIds))
  }, [selectedIds])

  const handleFolderClick = useCallback((folderId: string | null, folderName: string) => {
    setCurrentFolder(folderId)
    setSearchQuery('')

    // Update breadcrumbs
    if (folderId === null) {
      setBreadcrumbs([{ id: null, name: 'Root' }])
    } else {
      // Find folder path
      const findPath = (nodes: FolderNode[], targetId: string, path: { id: string | null; name: string }[]): { id: string | null; name: string }[] | null => {
        for (const node of nodes) {
          if (node.id === targetId) {
            return [...path, { id: node.id, name: node.name }]
          }
          if (node.children && node.children.length > 0) {
            const result = findPath(node.children as FolderNode[], targetId, [...path, { id: node.id, name: node.name }])
            if (result) return result
          }
        }
        return null
      }

      const path = findPath(folders, folderId, [{ id: null, name: 'Root' }])
      if (path) {
        setBreadcrumbs(path)
      } else {
        setBreadcrumbs([{ id: null, name: 'Root' }, { id: folderId, name: folderName }])
      }
    }
  }, [folders])

  const handleFileClick = useCallback((file: MediaFile, event: React.MouseEvent) => {
    if (multiSelect) {
      setSelectedFiles(prev => {
        const newSet = new Set(prev)
        if (event.ctrlKey || event.metaKey) {
          // Toggle selection
          if (newSet.has(file.id)) {
            newSet.delete(file.id)
          } else {
            newSet.add(file.id)
          }
        } else {
          // Replace selection
          newSet.clear()
          newSet.add(file.id)
        }

        // Notify parent
        const selectedArray = files.filter(f => newSet.has(f.id))
        onSelect?.(selectedArray)

        return newSet
      })
    } else {
      // Single select
      setSelectedFiles(new Set([file.id]))
      onSelect?.([file])
    }
  }, [files, multiSelect, onSelect])

  const handleFileDoubleClick = useCallback((file: MediaFile) => {
    // On double-click, confirm selection
    onSelect?.([file])
  }, [onSelect])

  const toggleFolderExpand = useCallback((folderId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    setExpandedFolders(prev => {
      const newSet = new Set(prev)
      if (newSet.has(folderId)) {
        newSet.delete(folderId)
      } else {
        newSet.add(folderId)
      }
      return newSet
    })
  }, [])

  const getFileIcon = (type: string): string => {
    if (type.startsWith('image/')) return '🖼️'
    if (type.startsWith('video/')) return '🎬'
    if (type.includes('pdf')) return '📄'
    if (type.includes('word') || type.includes('document')) return '📝'
    return '📁'
  }

  const renderFolderTree = (nodes: FolderNode[], depth: number = 0): React.ReactNode => {
    return nodes.map(node => {
      const hasChildren = node.children && node.children.length > 0
      const isExpanded = expandedFolders.has(node.id)
      const isActive = currentFolder === node.id

      return (
        <React.Fragment key={node.id}>
          <FolderItem
            $active={isActive}
            $depth={depth}
            onClick={() => handleFolderClick(node.id, node.name)}
          >
            {hasChildren && (
              <ExpandButton
                $expanded={isExpanded}
                onClick={(e) => toggleFolderExpand(node.id, e)}
              >
                ▶
              </ExpandButton>
            )}
            {!hasChildren && <span style={{ width: 16 }} />}
            <FolderIcon>{isActive ? '📂' : '📁'}</FolderIcon>
            <FolderName>{node.name}</FolderName>
          </FolderItem>
          {hasChildren && isExpanded && renderFolderTree(node.children as FolderNode[], depth + 1)}
        </React.Fragment>
      )
    })
  }

  return (
    <Container>
      <Sidebar>
        <SidebarHeader>
          📁 Folders
        </SidebarHeader>
        <FolderTree>
          <FolderItem
            $active={currentFolder === null}
            $depth={0}
            onClick={() => handleFolderClick(null, 'Root')}
          >
            <span style={{ width: 16 }} />
            <FolderIcon>{currentFolder === null ? '📂' : '📁'}</FolderIcon>
            <FolderName>All Files</FolderName>
          </FolderItem>
          {renderFolderTree(folders)}
        </FolderTree>
      </Sidebar>

      <MainContent>
        <Toolbar>
          <Breadcrumb>
            {breadcrumbs.map((crumb, index) => (
              <React.Fragment key={crumb.id ?? 'root'}>
                {index > 0 && <BreadcrumbSeparator>/</BreadcrumbSeparator>}
                <BreadcrumbItem
                  $clickable={index < breadcrumbs.length - 1}
                  onClick={() => {
                    if (index < breadcrumbs.length - 1) {
                      handleFolderClick(crumb.id, crumb.name)
                    }
                  }}
                >
                  {crumb.name}
                </BreadcrumbItem>
              </React.Fragment>
            ))}
          </Breadcrumb>
          <SearchInput
            type="text"
            placeholder="Search files..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </Toolbar>

        {loading ? (
          <LoadingOverlay>Loading...</LoadingOverlay>
        ) : files.length === 0 ? (
          <EmptyState>
            <EmptyIcon>📭</EmptyIcon>
            <EmptyText>
              {searchQuery ? 'No files match your search' : 'This folder is empty'}
            </EmptyText>
          </EmptyState>
        ) : (
          <FileGrid>
            {files.map(file => (
              <FileItem
                key={file.id}
                $selected={selectedFiles.has(file.id)}
                onClick={(e) => handleFileClick(file, e)}
                onDoubleClick={() => handleFileDoubleClick(file)}
              >
                <FileThumbnail>
                  {file.file_type.startsWith('image/') && file.thumbnail_url ? (
                    <ThumbnailImage src={file.thumbnail_url} alt={file.filename} />
                  ) : file.file_type.startsWith('image/') && file.url ? (
                    <ThumbnailImage src={file.url} alt={file.filename} />
                  ) : (
                    <ThumbnailIcon>{getFileIcon(file.file_type)}</ThumbnailIcon>
                  )}
                </FileThumbnail>
                <FileName>{file.original_filename || file.filename}</FileName>
                <FileSize>{adsAlertService.formatFileSize(file.file_size)}</FileSize>
              </FileItem>
            ))}
          </FileGrid>
        )}

        <StatusBar>
          <span>{files.length} file{files.length !== 1 ? 's' : ''}</span>
          {selectedFiles.size > 0 && (
            <SelectionInfo>
              {selectedFiles.size} selected
              {multiSelect && ' (Ctrl+click for multiple)'}
            </SelectionInfo>
          )}
        </StatusBar>
      </MainContent>
    </Container>
  )
}

export default MediaBrowser

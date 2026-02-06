import React, { useRef, useState } from 'react';
import { Upload, Folder, FileText, X } from 'lucide-react';

interface FolderUploadProps {
    onFilesSelected: (files: File[]) => void;
    disabled?: boolean;
}

interface FolderStructure {
    [studentName: string]: File[];
}

export const FolderUpload: React.FC<FolderUploadProps> = ({ onFilesSelected, disabled }) => {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [folderStructure, setFolderStructure] = useState<FolderStructure>({});
    const [isDragging, setIsDragging] = useState(false);

    const parseFolderStructure = (files: File[]): FolderStructure => {
        const structure: FolderStructure = {};

        // First pass: detect if we have a parent folder structure
        const allPaths = files.map(file => {
            const path = (file as any).webkitRelativePath || file.name;
            return path.split('/');
        });

        // Filter out hidden files
        const validPaths = allPaths.filter(parts => {
            const filename = parts[parts.length - 1];
            return !filename.startsWith('.') && !filename.startsWith('__');
        });

        // Check if all paths have at least 3 levels (parent/student/file.pdf)
        const hasParentFolder = validPaths.every(parts => parts.length >= 3);

        let folderOffset = 0;
        if (hasParentFolder && validPaths.length > 0) {
            // Check if they all share the same parent folder
            const parentFolders = new Set(validPaths.map(parts => parts[0]));
            if (parentFolders.size === 1) {
                // All files share the same parent folder, use second level as student name
                folderOffset = 1;
                console.log('Detected parent folder structure, using second level as student names');
            }
        }

        files.forEach(file => {
            // Get the webkitRelativePath which contains the folder structure
            const path = (file as any).webkitRelativePath || file.name;
            const parts = path.split('/');

            // Skip hidden files
            const filename = parts[parts.length - 1];
            if (filename.startsWith('.') || filename.startsWith('__')) {
                return;
            }

            if (parts.length > folderOffset + 1) {
                // Has folder structure: use appropriate level based on structure
                const studentName = parts[folderOffset];
                if (!structure[studentName]) {
                    structure[studentName] = [];
                }
                structure[studentName].push(file);
            } else {
                // Single file without proper folder structure
                if (!structure['Single Student']) {
                    structure['Single Student'] = [];
                }
                structure['Single Student'].push(file);
            }
        });

        return structure;
    };

    const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(event.target.files || []);
        if (files.length > 0) {
            const structure = parseFolderStructure(files);
            setFolderStructure(structure);
            onFilesSelected(files);
        }
    };

    const handleDrop = (event: React.DragEvent) => {
        event.preventDefault();
        setIsDragging(false);

        const items = Array.from(event.dataTransfer.items);
        const files: File[] = [];

        // Process dropped items
        items.forEach(item => {
            if (item.kind === 'file') {
                const file = item.getAsFile();
                if (file) files.push(file);
            }
        });

        if (files.length > 0) {
            const structure = parseFolderStructure(files);
            setFolderStructure(structure);
            onFilesSelected(files);
        }
    };

    const handleDragOver = (event: React.DragEvent) => {
        event.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleClear = () => {
        setFolderStructure({});
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const totalFiles = Object.values(folderStructure).reduce(
        (sum, files) => sum + files.length,
        0
    );

    return (
        <div className="space-y-4">
            {/* Upload Area */}
            <div
                className={`
          border-2 border-dashed rounded-lg p-8 text-center transition-colors
          ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-blue-400'}
        `}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => !disabled && fileInputRef.current?.click()}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    // @ts-ignore - webkitdirectory is not in TypeScript types
                    webkitdirectory="true"
                    directory="true"
                    className="hidden"
                    onChange={handleFileSelect}
                    disabled={disabled}
                />

                <div className="flex flex-col items-center gap-3">
                    <div className="p-3 bg-blue-100 rounded-full">
                        <Folder className="w-8 h-8 text-blue-600" />
                    </div>
                    <div>
                        <p className="text-lg font-medium text-gray-700">
                            Select Student Folders
                        </p>
                        <p className="text-sm text-gray-500 mt-1">
                            Click to browse or drag and drop folders here
                        </p>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-400">
                        <Upload className="w-4 h-4" />
                        <span>Supports: PDF, PNG, JPG, JPEG, TIFF</span>
                    </div>
                </div>
            </div>

            {/* Folder Preview */}
            {Object.keys(folderStructure).length > 0 && (
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                        <h3 className="font-medium text-gray-900">
                            Selected Folders ({Object.keys(folderStructure).length} student{Object.keys(folderStructure).length > 1 ? 's' : ''})
                        </h3>
                        <button
                            onClick={handleClear}
                            className="text-sm text-red-600 hover:text-red-700 flex items-center gap-1"
                            disabled={disabled}
                        >
                            <X className="w-4 h-4" />
                            Clear All
                        </button>
                    </div>

                    <div className="space-y-3 max-h-64 overflow-y-auto">
                        {Object.entries(folderStructure).map(([studentName, files]) => (
                            <div
                                key={studentName}
                                className="border border-gray-200 rounded-lg p-3 bg-gray-50"
                            >
                                <div className="flex items-center gap-2 mb-2">
                                    <Folder className="w-5 h-5 text-blue-600" />
                                    <span className="font-medium text-gray-900">{studentName}</span>
                                    <span className="text-sm text-gray-500">
                                        ({files.length} file{files.length > 1 ? 's' : ''})
                                    </span>
                                </div>
                                <div className="ml-7 space-y-1">
                                    {files.map((file, idx) => (
                                        <div
                                            key={idx}
                                            className="flex items-center gap-2 text-sm text-gray-600"
                                        >
                                            <FileText className="w-4 h-4 text-gray-400" />
                                            <span className="truncate">{file.name}</span>
                                            <span className="text-xs text-gray-400">
                                                ({(file.size / 1024).toFixed(1)} KB)
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-sm text-gray-600">
                            <span className="font-medium">Total:</span> {totalFiles} files across{' '}
                            {Object.keys(folderStructure).length} student folder{Object.keys(folderStructure).length > 1 ? 's' : ''}
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};

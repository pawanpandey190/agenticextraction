interface FileListProps {
  files: string[];
  onDelete?: (filename: string) => void;
  showDelete?: boolean;
}

function getFileIcon(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase();
  if (ext === 'pdf') return 'PDF';
  if (['png', 'jpg', 'jpeg', 'tiff', 'tif'].includes(ext || '')) return 'IMG';
  return 'DOC';
}

export function FileList({ files, onDelete, showDelete = true }: FileListProps) {
  if (files.length === 0) {
    return (
      <div className="text-center py-4 text-gray-500">
        No files uploaded yet
      </div>
    );
  }

  return (
    <ul className="divide-y divide-gray-200">
      {files.map((file) => (
        <li key={file} className="flex items-center justify-between py-3 px-2 hover:bg-gray-50">
          <div className="flex items-center space-x-3">
            <span className={`
              inline-flex items-center justify-center w-10 h-10 rounded text-xs font-bold
              ${getFileIcon(file) === 'PDF' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}
            `}>
              {getFileIcon(file)}
            </span>
            <span className="text-sm text-gray-700 truncate max-w-xs">{file}</span>
          </div>
          {showDelete && onDelete && (
            <button
              onClick={() => onDelete(file)}
              className="text-gray-400 hover:text-red-600 transition-colors"
              title="Remove file"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          )}
        </li>
      ))}
    </ul>
  );
}

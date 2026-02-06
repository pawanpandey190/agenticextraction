import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FolderUpload } from '../components/upload/FolderUpload';
import { api } from '../services/api';
import { ArrowLeft, Upload, AlertCircle } from 'lucide-react';

export function BatchUploadPage() {
    const navigate = useNavigate();
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [financialThreshold, setFinancialThreshold] = useState(15000);
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleFilesSelected = (files: File[]) => {
        setSelectedFiles(files);
        setError(null);
    };

    const handleUpload = async () => {
        if (selectedFiles.length === 0) {
            setError('Please select student folders first');
            return;
        }

        setIsUploading(true);
        setError(null);

        try {
            // Step 1: Upload batch folders
            const response = await api.uploadBatchFolders(selectedFiles, financialThreshold);

            // Step 2: Automatically start processing for each student
            const processingPromises = response.sessions.map(async (session) => {
                try {
                    await api.startProcessing(session.session_id);
                } catch (err) {
                    console.error(`Failed to start processing for ${session.student_name}:`, err);
                }
            });

            // Wait for all processing to start
            await Promise.all(processingPromises);

            // Navigate to batch results page
            navigate(`/batch/${response.batch_id}`);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Upload failed');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <div className="max-w-4xl mx-auto py-8 px-4">
                {/* Header */}
                <div className="mb-6">
                    <button
                        onClick={() => navigate('/')}
                        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
                    >
                        <ArrowLeft className="w-5 h-5" />
                        Back to Home
                    </button>
                    <h1 className="text-3xl font-bold text-gray-900">Batch Student Upload</h1>
                    <p className="text-gray-600 mt-2">
                        Upload folders containing documents for multiple students
                    </p>
                </div>

                {/* Important Instructions */}
                <div className="mb-6 bg-blue-50 border-2 border-blue-300 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                        <AlertCircle className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" />
                        <div>
                            <h3 className="font-semibold text-blue-900 mb-2">📁 How to Upload Multiple Students</h3>
                            <ol className="text-sm text-blue-800 space-y-2 list-decimal list-inside">
                                <li>
                                    <strong>Organize files:</strong> Create a parent folder (e.g., "Batch_Upload") containing one subfolder per student
                                </li>
                                <li>
                                    <strong>Click upload area below:</strong> Select the <strong>parent folder</strong> (not individual student folders)
                                </li>
                                <li>
                                    <strong>Review:</strong> Check that all students are detected correctly
                                </li>
                                <li>
                                    <strong>Upload:</strong> Click "Upload and Process Batch" to start
                                </li>
                            </ol>
                            <div className="mt-3 p-2 bg-white border border-blue-200 rounded">
                                <p className="text-xs text-blue-900 font-mono">
                                    Batch_Upload/ ← Select THIS folder<br />
                                    ├── John_Doe/<br />
                                    │   ├── passport.pdf<br />
                                    │   └── degree.pdf<br />
                                    └── Jane_Smith/<br />
                                    &nbsp;&nbsp;&nbsp;&nbsp;├── passport.pdf<br />
                                    &nbsp;&nbsp;&nbsp;&nbsp;└── degree.pdf
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Error Message */}
                {error && (
                    <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
                        <p className="text-red-800">{error}</p>
                    </div>
                )}

                {/* Upload Section */}
                <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
                    <FolderUpload
                        onFilesSelected={handleFilesSelected}
                        disabled={isUploading}
                    />
                </div>

                {/* Configuration */}
                <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Configuration</h3>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Financial Worthiness Threshold (EUR)
                        </label>
                        <input
                            type="number"
                            value={financialThreshold}
                            onChange={(e) => setFinancialThreshold(Number(e.target.value))}
                            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            min={0}
                            step={1000}
                            disabled={isUploading}
                        />
                        <p className="mt-2 text-sm text-gray-500">
                            Documents with amounts above this threshold will be marked as financially worthy
                        </p>
                    </div>
                </div>

                {/* Upload Button */}
                <button
                    onClick={handleUpload}
                    disabled={selectedFiles.length === 0 || isUploading}
                    className={`
            w-full py-4 px-6 text-lg font-medium rounded-lg transition-colors flex items-center justify-center gap-2
            ${selectedFiles.length > 0 && !isUploading
                            ? 'bg-blue-600 text-white hover:bg-blue-700'
                            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        }
          `}
                >
                    <Upload className="w-5 h-5" />
                    {isUploading ? 'Uploading and Starting Processing...' : 'Upload and Process Batch'}
                </button>

                {/* Processing Info */}
                <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-3">
                    <p className="text-sm text-green-800">
                        ✅ <strong>Auto-processing enabled:</strong> All students will automatically start processing after upload
                    </p>
                </div>
            </div>
        </div>
    );
}

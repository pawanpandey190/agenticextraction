import { test, expect } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

// Create a temporary test PDF file
const TEST_DIR = '/tmp/playwright-test-files';
const TEST_PDF_PATH = path.join(TEST_DIR, 'test-document.pdf');

// Minimal valid PDF structure
const MINIMAL_PDF = `%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >> endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer << /Size 4 /Root 1 0 R >>
startxref
196
%%EOF`;

// Helper to ensure test file exists
function ensureTestFile() {
  if (!fs.existsSync(TEST_DIR)) {
    fs.mkdirSync(TEST_DIR, { recursive: true });
  }
  if (!fs.existsSync(TEST_PDF_PATH)) {
    fs.writeFileSync(TEST_PDF_PATH, MINIMAL_PDF);
  }
}

// Create test file immediately on module load
ensureTestFile();

test.describe('File Upload Tests', () => {
  test('should upload a PDF file via API', async ({ request }) => {
    // Create a session
    const createResponse = await request.post('http://localhost:8000/api/sessions', {
      data: { financial_threshold: 15000 }
    });
    const { session_id } = await createResponse.json();

    // Upload a file
    const fileBuffer = fs.readFileSync(TEST_PDF_PATH);
    const uploadResponse = await request.post(
      `http://localhost:8000/api/sessions/${session_id}/documents`,
      {
        multipart: {
          files: {
            name: 'test-document.pdf',
            mimeType: 'application/pdf',
            buffer: fileBuffer,
          },
        },
      }
    );

    expect(uploadResponse.ok()).toBeTruthy();
    const uploadData = await uploadResponse.json();
    expect(uploadData.uploaded_files).toContain('test-document.pdf');
    expect(uploadData.total_files).toBe(1);
  });

  test('should list uploaded documents via API', async ({ request }) => {
    // Create a session
    const createResponse = await request.post('http://localhost:8000/api/sessions', {
      data: {}
    });
    const { session_id } = await createResponse.json();

    // Upload a file
    const fileBuffer = fs.readFileSync(TEST_PDF_PATH);
    await request.post(
      `http://localhost:8000/api/sessions/${session_id}/documents`,
      {
        multipart: {
          files: {
            name: 'test-document.pdf',
            mimeType: 'application/pdf',
            buffer: fileBuffer,
          },
        },
      }
    );

    // List documents
    const listResponse = await request.get(
      `http://localhost:8000/api/sessions/${session_id}/documents`
    );

    expect(listResponse.ok()).toBeTruthy();
    const listData = await listResponse.json();
    expect(listData.files).toContain('test-document.pdf');
    expect(listData.total).toBe(1);
  });

  test('should delete an uploaded document via API', async ({ request }) => {
    // Create a session
    const createResponse = await request.post('http://localhost:8000/api/sessions', {
      data: {}
    });
    const { session_id } = await createResponse.json();

    // Upload a file
    const fileBuffer = fs.readFileSync(TEST_PDF_PATH);
    await request.post(
      `http://localhost:8000/api/sessions/${session_id}/documents`,
      {
        multipart: {
          files: {
            name: 'test-document.pdf',
            mimeType: 'application/pdf',
            buffer: fileBuffer,
          },
        },
      }
    );

    // Delete the document
    const deleteResponse = await request.delete(
      `http://localhost:8000/api/sessions/${session_id}/documents/test-document.pdf`
    );
    expect(deleteResponse.status()).toBe(204);

    // Verify it's deleted
    const listResponse = await request.get(
      `http://localhost:8000/api/sessions/${session_id}/documents`
    );
    const listData = await listResponse.json();
    expect(listData.files).not.toContain('test-document.pdf');
    expect(listData.total).toBe(0);
  });

  test('should update session after file upload', async ({ request }) => {
    // Create a session
    const createResponse = await request.post('http://localhost:8000/api/sessions', {
      data: {}
    });
    const { session_id } = await createResponse.json();

    // Upload a file
    const fileBuffer = fs.readFileSync(TEST_PDF_PATH);
    await request.post(
      `http://localhost:8000/api/sessions/${session_id}/documents`,
      {
        multipart: {
          files: {
            name: 'test-document.pdf',
            mimeType: 'application/pdf',
            buffer: fileBuffer,
          },
        },
      }
    );

    // Get session details
    const getResponse = await request.get(
      `http://localhost:8000/api/sessions/${session_id}`
    );

    const session = await getResponse.json();
    expect(session.uploaded_files).toContain('test-document.pdf');
    expect(session.total_files).toBe(1);
    expect(session.status).toBe('uploading');
  });

  test('should reject non-allowed file types via API', async ({ request }) => {
    // Create a session
    const createResponse = await request.post('http://localhost:8000/api/sessions', {
      data: {}
    });
    const { session_id } = await createResponse.json();

    // Try to upload a non-allowed file type
    const uploadResponse = await request.post(
      `http://localhost:8000/api/sessions/${session_id}/documents`,
      {
        multipart: {
          files: {
            name: 'test-file.exe',
            mimeType: 'application/octet-stream',
            buffer: Buffer.from('test content'),
          },
        },
      }
    );

    expect(uploadResponse.status()).toBe(400);
  });

  test('should handle file upload via browser dropzone', async ({ page }) => {
    await page.goto('/');

    // Wait for session creation
    await expect(page.getByText('Upload Documents')).toBeVisible({ timeout: 10000 });

    // Find the file input (it's hidden but we can still interact with it)
    const fileInput = page.locator('input[type="file"]');

    // Set the file
    await fileInput.setInputFiles(TEST_PDF_PATH);

    // Should show pending files
    await expect(page.getByText('Pending upload')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('test-document.pdf')).toBeVisible();

    // Click upload button
    await page.getByRole('button', { name: 'Upload Files' }).click();

    // Wait for upload to complete - file should move from pending to uploaded
    await expect(page.getByText('Uploaded Files (1)')).toBeVisible({ timeout: 10000 });

    // The Start Analysis button should now be enabled
    const startButton = page.getByRole('button', { name: 'Start Analysis' });
    await expect(startButton).toBeEnabled();
  });

  test('should allow removing pending files before upload', async ({ page }) => {
    await page.goto('/');

    // Wait for session creation
    await expect(page.getByText('Upload Documents')).toBeVisible({ timeout: 10000 });

    // Add a file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(TEST_PDF_PATH);

    // Should show pending files
    await expect(page.getByText('Pending upload')).toBeVisible();

    // Remove the file
    await page.getByRole('button', { name: 'Remove' }).click();

    // Pending section should disappear
    await expect(page.getByText('Pending upload')).not.toBeVisible();
  });
});

test.describe('Processing Flow', () => {
  test('should start processing when files are uploaded', async ({ request }) => {
    // Create a session
    const createResponse = await request.post('http://localhost:8000/api/sessions', {
      data: {}
    });
    const { session_id } = await createResponse.json();

    // Upload a file
    const fileBuffer = fs.readFileSync(TEST_PDF_PATH);
    await request.post(
      `http://localhost:8000/api/sessions/${session_id}/documents`,
      {
        multipart: {
          files: {
            name: 'test-document.pdf',
            mimeType: 'application/pdf',
            buffer: fileBuffer,
          },
        },
      }
    );

    // Start processing
    const processResponse = await request.post(
      `http://localhost:8000/api/sessions/${session_id}/process`
    );

    expect(processResponse.status()).toBe(202);
    const processData = await processResponse.json();
    expect(processData.message).toBe('Processing started');
    expect(processData.progress_url).toContain('/progress');
  });

  test('should reject processing with no files', async ({ request }) => {
    // Create a session
    const createResponse = await request.post('http://localhost:8000/api/sessions', {
      data: {}
    });
    const { session_id } = await createResponse.json();

    // Try to start processing without files
    const processResponse = await request.post(
      `http://localhost:8000/api/sessions/${session_id}/process`
    );

    expect(processResponse.status()).toBe(400);
    const errorData = await processResponse.json();
    expect(errorData.detail).toContain('No documents');
  });
});

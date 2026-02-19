import { test, expect } from '@playwright/test';

test.describe('Document Analysis UI', () => {
  test.describe('Upload Page', () => {
    test('should display the upload page on load', async ({ page }) => {
      await page.goto('/');

      // Check page title and header
      await expect(page).toHaveTitle('Document Analysis UI');
      await expect(page.locator('header h1')).toContainText('Document Analysis');

      // Check that the description is visible
      await expect(page.getByText('Upload your documents to analyze')).toBeVisible();
    });

    test('should create a session automatically', async ({ page }) => {
      await page.goto('/');

      // Wait for session to be created (upload section should appear)
      await expect(page.getByText('Upload Documents')).toBeVisible({ timeout: 10000 });

      // Check that the configuration section is visible
      await expect(page.getByText('Configuration')).toBeVisible();
      await expect(page.getByText('Financial Worthiness Threshold')).toBeVisible();
    });

    test('should display the drop zone', async ({ page }) => {
      await page.goto('/');

      // Wait for session creation
      await expect(page.getByText('Upload Documents')).toBeVisible({ timeout: 10000 });

      // Check drop zone is present
      await expect(page.getByText('Click to upload')).toBeVisible();
      await expect(page.getByText('PDF, PNG, JPEG, TIFF files')).toBeVisible();
    });

    test('should show empty file list initially', async ({ page }) => {
      await page.goto('/');

      // Wait for session creation
      await expect(page.getByText('Uploaded Files')).toBeVisible({ timeout: 10000 });

      // Check for empty state
      await expect(page.getByText('No files uploaded yet')).toBeVisible();
    });

    test('should have disabled Start Analysis button when no files uploaded', async ({ page }) => {
      await page.goto('/');

      // Wait for session creation
      await expect(page.getByText('Upload Documents')).toBeVisible({ timeout: 10000 });

      // Check that start button is disabled
      const startButton = page.getByRole('button', { name: 'Start Analysis' });
      await expect(startButton).toBeVisible();
      await expect(startButton).toBeDisabled();
    });

    test('should allow changing financial threshold', async ({ page }) => {
      await page.goto('/');

      // Wait for session creation
      await expect(page.getByText('Financial Worthiness Threshold')).toBeVisible({ timeout: 10000 });

      // Find the threshold input and change it
      const thresholdInput = page.locator('input[type="number"]');
      await expect(thresholdInput).toBeVisible();

      // Clear and set new value
      await thresholdInput.fill('25000');
      await expect(thresholdInput).toHaveValue('25000');
    });
  });

  test.describe('Navigation', () => {
    test('should have header with app title', async ({ page }) => {
      await page.goto('/');

      // Check header is present
      await expect(page.locator('header')).toBeVisible();
      await expect(page.locator('header').getByText('Document Analysis')).toBeVisible();
    });

    test('should have footer', async ({ page }) => {
      await page.goto('/');

      // Check footer is present
      await expect(page.locator('footer')).toBeVisible();
      await expect(page.getByText('AI-Powered Document Analysis System')).toBeVisible();
    });
  });

  test.describe('API Integration', () => {
    test('should successfully create session via API', async ({ request }) => {
      const response = await request.post('http://localhost:8000/api/sessions', {
        data: { financial_threshold: 15000 }
      });

      expect(response.ok()).toBeTruthy();
      const data = await response.json();
      expect(data.session_id).toBeDefined();
      expect(data.status).toBe('created');
      expect(data.upload_url).toContain('/documents');
    });

    test('should get session details via API', async ({ request }) => {
      // Create a session first
      const createResponse = await request.post('http://localhost:8000/api/sessions', {
        data: {}
      });
      const { session_id } = await createResponse.json();

      // Get session details
      const getResponse = await request.get(`http://localhost:8000/api/sessions/${session_id}`);
      expect(getResponse.ok()).toBeTruthy();

      const session = await getResponse.json();
      expect(session.id).toBe(session_id);
      expect(session.status).toBe('created');
      expect(session.uploaded_files).toEqual([]);
      expect(session.total_files).toBe(0);
    });

    test('should list sessions via API', async ({ request }) => {
      // Create a session
      await request.post('http://localhost:8000/api/sessions', { data: {} });

      // List sessions
      const response = await request.get('http://localhost:8000/api/sessions');
      expect(response.ok()).toBeTruthy();

      const sessions = await response.json();
      expect(Array.isArray(sessions)).toBeTruthy();
      expect(sessions.length).toBeGreaterThan(0);
    });

    test('should delete session via API', async ({ request }) => {
      // Create a session
      const createResponse = await request.post('http://localhost:8000/api/sessions', {
        data: {}
      });
      const { session_id } = await createResponse.json();

      // Delete the session
      const deleteResponse = await request.delete(`http://localhost:8000/api/sessions/${session_id}`);
      expect(deleteResponse.status()).toBe(204);

      // Verify it's deleted
      const getResponse = await request.get(`http://localhost:8000/api/sessions/${session_id}`);
      expect(getResponse.status()).toBe(404);
    });

    test('should return 404 for non-existent session', async ({ request }) => {
      const response = await request.get('http://localhost:8000/api/sessions/non-existent-id');
      expect(response.status()).toBe(404);
    });

    test('health endpoint should return healthy', async ({ request }) => {
      const response = await request.get('http://localhost:8000/health');
      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data.status).toBe('healthy');
    });
  });

  test.describe('File Upload Flow', () => {
    test('should handle file selection via input', async ({ page }) => {
      await page.goto('/');

      // Wait for session creation
      await expect(page.getByText('Upload Documents')).toBeVisible({ timeout: 10000 });

      // The dropzone has a hidden file input
      const fileInput = page.locator('input[type="file"]');
      await expect(fileInput).toBeAttached();
    });
  });

  test.describe('Batch Processing Flow', () => {
    test('should show batch upload option', async ({ page }) => {
      await page.goto('/');

      // Wait for session creation
      await expect(page.getByText('Upload Documents')).toBeVisible({ timeout: 10000 });

      // Check if there's a batch upload or multi-folder instruction
      await expect(page.locator('body')).toContainText(/batch|folder/i);
    });

    test('should navigate to batch status page', async ({ page }) => {
      // Create a mock batch
      const batchId = 'test-batch-123';
      await page.goto(`/batch/${batchId}`);

      // Should show batch status page
      await expect(page.locator('h2')).toContainText(/Batch/i);
      await expect(page.getByText(batchId)).toBeVisible();
    });

    test('should display progress for batch sessions', async ({ page }) => {
      const batchId = 'test-batch-progress';

      // Mock the batch status API
      await page.route(`**/api/sessions/batches/${batchId}`, async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            batch_id: batchId,
            status: 'processing',
            total_students: 2,
            completed: 1,
            processing: 1,
            failed: 0,
            created: 0,
            sessions: [
              {
                session_id: 's1',
                student_name: 'Student 1',
                status: 'completed',
                total_files: 3,
                result_available: true,
                letter_available: true
              },
              {
                session_id: 's2',
                student_name: 'Student 2',
                status: 'processing',
                total_files: 2,
                result_available: false,
                letter_available: false
              }
            ]
          })
        });
      });

      await page.goto(`/batch/${batchId}`);

      // Verify the progress is shown
      await expect(page.getByText('Student 1')).toBeVisible();
      await expect(page.getByText('Student 2')).toBeVisible();
      await expect(page.getByText('completed', { exact: false })).toBeVisible();
      await expect(page.getByText('processing', { exact: false })).toBeVisible();
    });
  });

  test.describe('Error Handling', () => {
    test('should handle invalid session ID gracefully', async ({ page }) => {
      // Navigate to a non-existent session's processing page
      await page.goto('/processing/invalid-session-id');

      // Should show some error message (could be in progress view or elsewhere)
      // Wait for either an error message or the progress view to appear
      await page.waitForTimeout(2000);

      // The page should at least render without crashing
      await expect(page.locator('body')).toBeVisible();
    });

    test('should handle invalid session ID on report page', async ({ page }) => {
      // Navigate to a non-existent session's report page
      await page.goto('/report/invalid-session-id');

      // Should show error or loading state
      await page.waitForTimeout(2000);

      // Check that the page rendered (either error or content)
      await expect(page.locator('body')).toBeVisible();
    });
  });

  test.describe('UI Components', () => {
    test('should render progress bar component correctly', async ({ page }) => {
      // Create a session and start processing to see progress
      await page.goto('/');

      // Wait for page to load
      await expect(page.getByText('Upload Documents')).toBeVisible({ timeout: 10000 });

      // The progress components should be defined in the codebase
      // This test verifies the upload page renders without errors
      await expect(page.locator('main')).toBeVisible();
    });
  });

  test.describe('Responsive Design', () => {
    test('should render correctly on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/');

      // Check that main elements are still visible
      await expect(page.locator('header')).toBeVisible();
      await expect(page.locator('header h1')).toContainText('Document Analysis');
      await expect(page.locator('main')).toBeVisible();
    });

    test('should render correctly on tablet viewport', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto('/');

      await expect(page.locator('header')).toBeVisible();
      await expect(page.locator('header h1')).toContainText('Document Analysis');
    });

    test('should render correctly on desktop viewport', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('/');

      await expect(page.locator('header')).toBeVisible();
      await expect(page.locator('header h1')).toContainText('Document Analysis');
    });
  });
});

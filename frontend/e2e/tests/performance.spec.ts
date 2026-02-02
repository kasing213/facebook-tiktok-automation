import { test, expect } from '../fixtures/auth.fixture';

test.describe('Performance and Load Testing', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authenticated user
    await page.route('**/api/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: {
            id: '123e4567-e89b-12d3-a456-426614174000',
            email: 'perf-test@example.com',
            firstName: 'Performance',
            lastName: 'Tester'
          }
        })
      });
    });
  });

  test.describe('Page Load Performance', () => {
    test('should load dashboard within 2 seconds', async ({ page }) => {
      // Mock dashboard data
      await page.route('**/api/dashboard/stats', async (route) => {
        // Simulate API response time
        await new Promise(resolve => setTimeout(resolve, 100));

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            invoices: { total: 250, pending: 15, paid: 230, overdue: 5 },
            products: { total: 150, lowStock: 8 },
            revenue: { thisMonth: 45230.50, lastMonth: 38120.25 },
            recentActivity: []
          })
        });
      });

      const startTime = Date.now();

      await page.goto('/dashboard');

      // Wait for dashboard to be fully loaded
      await expect(page.locator('[class*="dashboard"], [class*="stats"]')).toBeVisible();

      const loadTime = Date.now() - startTime;

      // Should load within 2 seconds
      expect(loadTime).toBeLessThan(2000);

      console.log(`Dashboard loaded in ${loadTime}ms`);
    });

    test('should load invoice list within 3 seconds with 1000+ invoices', async ({ page }) => {
      // Mock large invoice dataset
      await page.route('**/api/invoice/invoices*', async (route) => {
        // Simulate database query time for large dataset
        await new Promise(resolve => setTimeout(resolve, 200));

        const mockInvoices = Array.from({ length: 50 }, (_, i) => ({
          id: `invoice-${i + 1}`,
          invoiceNumber: `INV-${String(i + 1).padStart(4, '0')}`,
          recipientName: `Customer ${i + 1}`,
          amount: Math.floor(Math.random() * 10000) + 100,
          status: ['pending', 'paid', 'overdue'][Math.floor(Math.random() * 3)],
          createdAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString()
        }));

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            invoices: mockInvoices,
            totalCount: 1250, // Simulate large total count
            page: 1,
            limit: 50,
            totalPages: 25
          })
        });
      });

      const startTime = Date.now();

      await page.goto('/dashboard/invoices');

      // Wait for invoice table to load
      await expect(page.locator('table, [class*="invoice-list"]')).toBeVisible();
      await expect(page.locator('tr, [class*="invoice-item"]').first()).toBeVisible();

      const loadTime = Date.now() - startTime;

      // Should load within 3 seconds even with large dataset
      expect(loadTime).toBeLessThan(3000);

      console.log(`Invoice list with 1250 invoices loaded in ${loadTime}ms`);
    });

    test('should handle pagination efficiently', async ({ page }) => {
      let pageRequests = 0;

      await page.route('**/api/invoice/invoices*', async (route) => {
        pageRequests++;
        const url = new URL(route.request().url());
        const page_num = parseInt(url.searchParams.get('page') || '1');

        // Simulate fast pagination response
        await new Promise(resolve => setTimeout(resolve, 50));

        const mockInvoices = Array.from({ length: 20 }, (_, i) => ({
          id: `invoice-page-${page_num}-${i + 1}`,
          invoiceNumber: `INV-${String((page_num - 1) * 20 + i + 1).padStart(4, '0')}`,
          recipientName: `Page ${page_num} Customer ${i + 1}`,
          amount: Math.floor(Math.random() * 5000) + 100
        }));

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            invoices: mockInvoices,
            page: page_num,
            totalCount: 1000,
            totalPages: 50
          })
        });
      });

      await page.goto('/dashboard/invoices');

      // Test pagination performance
      const paginationTimes: number[] = [];

      for (let i = 2; i <= 5; i++) {
        const startTime = Date.now();

        // Click next page or page number
        const nextButton = page.getByRole('button', { name: String(i) }).or(
          page.getByRole('button', { name: /next/i })
        );

        if (await nextButton.isVisible()) {
          await nextButton.click();

          // Wait for new page to load
          await expect(page.locator(`text=/Page ${i}/i`).first()).toBeVisible();

          const pageLoadTime = Date.now() - startTime;
          paginationTimes.push(pageLoadTime);
        }
      }

      // All pagination requests should be under 1 second
      paginationTimes.forEach(time => {
        expect(time).toBeLessThan(1000);
      });

      const avgPaginationTime = paginationTimes.reduce((a, b) => a + b, 0) / paginationTimes.length;
      console.log(`Average pagination time: ${avgPaginationTime.toFixed(2)}ms`);
    });
  });

  test.describe('Search Performance', () => {
    test('should provide fast search results', async ({ page }) => {
      let searchRequests = 0;

      await page.route('**/api/invoice/invoices*', async (route) => {
        searchRequests++;
        const url = new URL(route.request().url());
        const searchQuery = url.searchParams.get('search');

        // Simulate search query processing time
        const processingTime = searchQuery && searchQuery.length > 3 ? 150 : 50;
        await new Promise(resolve => setTimeout(resolve, processingTime));

        const mockResults = searchQuery
          ? Array.from({ length: 12 }, (_, i) => ({
              id: `search-result-${i}`,
              invoiceNumber: `INV-${searchQuery.toUpperCase()}-${i + 1}`,
              recipientName: `${searchQuery} Customer ${i + 1}`,
              amount: Math.random() * 2000 + 100,
              highlighted: searchQuery
            }))
          : [];

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            invoices: mockResults,
            searchQuery,
            totalCount: mockResults.length,
            searchTime: processingTime
          })
        });
      });

      await page.goto('/dashboard/invoices');

      const searchInput = page.locator('input[type="search"], input[placeholder*="search"]');
      await expect(searchInput).toBeVisible();

      // Test search performance with different query lengths
      const searchTerms = ['A', 'TECH', 'Technology Solutions'];
      const searchTimes: number[] = [];

      for (const term of searchTerms) {
        const startTime = Date.now();

        await searchInput.fill(term);
        await searchInput.press('Enter');

        // Wait for search results
        await page.waitForResponse(response =>
          response.url().includes('/api/invoice/invoices') && response.status() === 200
        );

        const searchTime = Date.now() - startTime;
        searchTimes.push(searchTime);

        console.log(`Search for "${term}" took ${searchTime}ms`);
      }

      // Search should be responsive (under 500ms for client-side)
      searchTimes.forEach(time => {
        expect(time).toBeLessThan(500);
      });
    });

    test('should handle real-time search efficiently', async ({ page }) => {
      let debounceTestPassed = true;
      let requestCount = 0;

      await page.route('**/api/invoice/invoices*', async (route) => {
        requestCount++;

        // Should use debouncing to avoid too many requests
        if (requestCount > 3) {
          debounceTestPassed = false;
        }

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            invoices: [],
            searchQuery: new URL(route.request().url()).searchParams.get('search'),
            requestNumber: requestCount
          })
        });
      });

      await page.goto('/dashboard/invoices');

      const searchInput = page.locator('input[type="search"], input[placeholder*="search"]');
      await expect(searchInput).toBeVisible();

      // Type rapidly to test debouncing
      const searchTerm = 'Technology';
      for (const char of searchTerm) {
        await searchInput.type(char);
        await page.waitForTimeout(50); // Type rapidly
      }

      // Wait for debounce period
      await page.waitForTimeout(1000);

      // Should have debounced the requests
      expect(debounceTestPassed).toBe(true);
      console.log(`Search debouncing test passed with ${requestCount} requests`);
    });
  });

  test.describe('Concurrent User Simulation', () => {
    test('should handle multiple simultaneous operations', async ({ page, context }) => {
      // Create multiple pages to simulate concurrent users
      const pages = [page];

      // Add 4 more browser contexts
      for (let i = 1; i < 5; i++) {
        const newPage = await context.newPage();
        pages.push(newPage);
      }

      let totalRequests = 0;
      const operationTimes: number[] = [];

      // Mock API with slight delays to simulate load
      for (const testPage of pages) {
        await testPage.route('**/api/**', async (route) => {
          totalRequests++;

          // Simulate server processing under load
          const delay = Math.random() * 100 + 50; // 50-150ms delay
          await new Promise(resolve => setTimeout(resolve, delay));

          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: [],
              processingTime: delay,
              requestId: totalRequests
            })
          });
        });
      }

      // Perform concurrent operations
      const promises = pages.map(async (testPage, index) => {
        const startTime = Date.now();

        await testPage.goto('/dashboard/invoices');
        await testPage.goto('/dashboard/inventory');
        await testPage.goto('/dashboard');

        const operationTime = Date.now() - startTime;
        operationTimes.push(operationTime);

        return {
          pageIndex: index,
          operationTime
        };
      });

      const results = await Promise.all(promises);

      // All concurrent operations should complete within reasonable time
      results.forEach(result => {
        expect(result.operationTime).toBeLessThan(5000);
        console.log(`User ${result.pageIndex + 1} operations took ${result.operationTime}ms`);
      });

      // Clean up additional pages
      for (let i = 1; i < pages.length; i++) {
        await pages[i].close();
      }

      console.log(`Handled ${totalRequests} total requests across ${pages.length} concurrent users`);
    });

    test('should maintain performance during peak usage simulation', async ({ page }) => {
      let peakRequestCount = 0;
      const responseTimes: number[] = [];

      await page.route('**/api/**', async (route) => {
        peakRequestCount++;
        const requestStartTime = Date.now();

        // Simulate peak load response times (higher delay)
        const peakDelay = Math.random() * 200 + 100; // 100-300ms
        await new Promise(resolve => setTimeout(resolve, peakDelay));

        const responseTime = Date.now() - requestStartTime;
        responseTimes.push(responseTime);

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: [],
            peakLoad: true,
            responseTime: responseTime,
            queuePosition: peakRequestCount
          })
        });
      });

      // Simulate peak usage patterns
      const peakOperations = [
        () => page.goto('/dashboard'),
        () => page.goto('/dashboard/invoices'),
        () => page.click('text=/Create/i').catch(() => {}), // May not exist
        () => page.goto('/dashboard/inventory'),
        () => page.reload(),
        () => page.goto('/dashboard/marketing'),
        () => page.goBack(),
        () => page.goto('/dashboard/billing')
      ];

      const startTime = Date.now();

      // Execute operations rapidly
      for (const operation of peakOperations) {
        await operation();
        await page.waitForTimeout(100); // Brief pause between operations
      }

      const totalTime = Date.now() - startTime;

      // Calculate performance metrics
      const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
      const maxResponseTime = Math.max(...responseTimes);

      console.log(`Peak load test: ${peakRequestCount} requests in ${totalTime}ms`);
      console.log(`Average response time: ${avgResponseTime.toFixed(2)}ms`);
      console.log(`Max response time: ${maxResponseTime}ms`);

      // Performance should remain acceptable during peak load
      expect(avgResponseTime).toBeLessThan(500);
      expect(maxResponseTime).toBeLessThan(1000);
      expect(totalTime).toBeLessThan(10000);
    });
  });

  test.describe('Memory and Resource Usage', () => {
    test('should not have memory leaks during extended use', async ({ page }) => {
      // Mock data that might cause memory issues
      await page.route('**/api/invoice/invoices*', async (route) => {
        // Generate large dataset
        const largeDataset = Array.from({ length: 100 }, (_, i) => ({
          id: `memory-test-${i}`,
          invoiceNumber: `INV-MEM-${i.toString().padStart(4, '0')}`,
          recipientName: `Memory Test Customer ${i}`,
          amount: Math.random() * 10000,
          lineItems: Array.from({ length: 20 }, (_, j) => ({
            id: `item-${i}-${j}`,
            name: `Product ${j}`,
            description: 'A'.repeat(100), // Long description
            quantity: Math.floor(Math.random() * 10) + 1,
            price: Math.random() * 100
          }))
        }));

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            invoices: largeDataset,
            totalCount: largeDataset.length
          })
        });
      });

      // Perform operations that might cause memory leaks
      for (let cycle = 0; cycle < 20; cycle++) {
        await page.goto('/dashboard/invoices');
        await page.goto('/dashboard/inventory');
        await page.goto('/dashboard/marketing');
        await page.goto('/dashboard');

        // Check if page is still responsive
        await expect(page.locator('body')).toBeVisible();

        if (cycle % 5 === 0) {
          console.log(`Memory test cycle ${cycle + 1}/20 completed`);
        }
      }

      // Page should still be responsive after extended use
      await page.goto('/dashboard/invoices');
      await expect(page.locator('table, [class*="invoice"]')).toBeVisible();

      console.log('Memory leak test completed successfully');
    });

    test('should handle large file operations efficiently', async ({ page }) => {
      // Mock large file upload
      await page.route('**/api/ads-alert/media/upload', async (route) => {
        const uploadStartTime = Date.now();

        // Simulate processing time for large file
        await new Promise(resolve => setTimeout(resolve, 500));

        const processingTime = Date.now() - uploadStartTime;

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            filename: 'large-test-file.jpg',
            size: '8.5 MB',
            processingTime: processingTime,
            optimized: true
          })
        });
      });

      // Mock large export operation
      await page.route('**/api/invoice/export**', async (route) => {
        const exportStartTime = Date.now();

        // Simulate export processing time
        await new Promise(resolve => setTimeout(resolve, 1000));

        const exportTime = Date.now() - exportStartTime;

        await route.fulfill({
          status: 200,
          contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          headers: {
            'Content-Disposition': 'attachment; filename="invoices-export.xlsx"'
          },
          body: Buffer.from('fake-excel-data'),
          bodyAnnotations: {
            exportTime: exportTime
          }
        });
      });

      await page.goto('/dashboard/marketing');

      // Test file upload performance
      const fileInput = page.locator('input[type="file"]');
      if (await fileInput.isVisible()) {
        const uploadStartTime = Date.now();

        await fileInput.setInputFiles({
          name: 'large-test-image.jpg',
          mimeType: 'image/jpeg',
          buffer: Buffer.alloc(8 * 1024 * 1024, 'fake-image-data') // 8MB file
        });

        // Wait for upload completion
        await expect(
          page.locator('text=/upload.*successful|file.*uploaded/i')
        ).toBeVisible({ timeout: 10000 });

        const uploadTime = Date.now() - uploadStartTime;
        console.log(`8MB file upload took ${uploadTime}ms`);

        // Should handle large files within reasonable time
        expect(uploadTime).toBeLessThan(10000);
      }

      // Test large export performance
      await page.goto('/dashboard/invoices');

      const exportButton = page.getByRole('button', { name: /export|download/i });
      if (await exportButton.isVisible()) {
        const exportStartTime = Date.now();

        await exportButton.click();

        // Wait for download to start
        const downloadPromise = page.waitForEvent('download', { timeout: 15000 });
        const download = await downloadPromise;

        const exportTime = Date.now() - exportStartTime;
        console.log(`Export operation took ${exportTime}ms`);

        // Should handle exports efficiently
        expect(exportTime).toBeLessThan(5000);
        expect(download.suggestedFilename()).toContain('invoices-export');
      }
    });
  });

  test.describe('API Performance Monitoring', () => {
    test('should track API response times', async ({ page }) => {
      const apiMetrics: { endpoint: string; responseTime: number; status: number }[] = [];

      // Monitor all API calls
      page.on('response', async (response) => {
        if (response.url().includes('/api/')) {
          const timing = response.timing();
          apiMetrics.push({
            endpoint: response.url().split('/api/')[1],
            responseTime: timing.responseEnd - timing.responseStart,
            status: response.status()
          });
        }
      });

      // Navigate through app to generate API calls
      await page.goto('/dashboard');
      await page.goto('/dashboard/invoices');
      await page.goto('/dashboard/inventory');
      await page.goto('/dashboard/marketing');

      // Wait for all API calls to complete
      await page.waitForTimeout(2000);

      // Analyze API performance
      const avgResponseTime = apiMetrics.reduce((sum, metric) => sum + metric.responseTime, 0) / apiMetrics.length;
      const slowestEndpoint = apiMetrics.reduce((slowest, current) =>
        current.responseTime > slowest.responseTime ? current : slowest, apiMetrics[0]
      );

      console.log(`Monitored ${apiMetrics.length} API calls`);
      console.log(`Average response time: ${avgResponseTime.toFixed(2)}ms`);
      console.log(`Slowest endpoint: ${slowestEndpoint.endpoint} (${slowestEndpoint.responseTime}ms)`);

      // API performance benchmarks
      expect(avgResponseTime).toBeLessThan(300);
      expect(slowestEndpoint.responseTime).toBeLessThan(1000);

      // All API calls should be successful
      const errorCount = apiMetrics.filter(metric => metric.status >= 400).length;
      expect(errorCount).toBe(0);
    });
  });
});
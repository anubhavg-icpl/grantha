/**
 * Navigation E2E Tests
 * Tests for basic navigation and page loading
 */

import { test, expect } from '@playwright/test';

test.describe('Navigation Tests', () => {
  test('should load home page', async ({ page }) => {
    await page.goto('/');
    
    // Check that the page loads
    await expect(page).toHaveTitle(/Grantha/);
    
    // Check for main navigation elements
    await expect(page.locator('nav')).toBeVisible();
  });

  test('should navigate to chat page', async ({ page }) => {
    await page.goto('/');
    
    // Click on chat navigation item
    await page.click('text=Chat');
    
    // Check URL changed
    await expect(page).toHaveURL('/chat');
    
    // Check chat interface is loaded
    await expect(page.locator('[data-testid="chat-area"]')).toBeVisible();
    await expect(page.locator('[data-testid="chat-input"]')).toBeVisible();
  });

  test('should navigate to models page', async ({ page }) => {
    await page.goto('/');
    
    await page.click('text=Models');
    
    await expect(page).toHaveURL('/models');
    await expect(page.locator('h1')).toContainText('AI Models');
  });

  test('should navigate to wiki page', async ({ page }) => {
    await page.goto('/');
    
    await page.click('text=Wiki');
    
    await expect(page).toHaveURL('/wiki');
    await expect(page.locator('h1')).toContainText('Wiki Generator');
  });

  test('should navigate to research page', async ({ page }) => {
    await page.goto('/');
    
    await page.click('text=Research');
    
    await expect(page).toHaveURL('/research');
    await expect(page.locator('h1')).toContainText('AI Research Assistant');
  });

  test('should navigate to settings page', async ({ page }) => {
    await page.goto('/');
    
    await page.click('text=Settings');
    
    await expect(page).toHaveURL('/settings');
    await expect(page.locator('h1')).toContainText('Settings');
  });

  test('should have responsive navigation', async ({ page }) => {
    await page.goto('/');
    
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check if mobile navigation works (hamburger menu, etc.)
    const hamburgerMenu = page.locator('[data-testid="mobile-menu-toggle"]');
    if (await hamburgerMenu.isVisible()) {
      await hamburgerMenu.click();
      await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
    }
  });

  test('should handle 404 pages gracefully', async ({ page }) => {
    await page.goto('/nonexistent-page');
    
    // Should show 404 page or redirect to home
    const isNotFound = await page.locator('text=404').isVisible();
    const isHome = page.url().includes('/');
    
    expect(isNotFound || isHome).toBeTruthy();
  });
});
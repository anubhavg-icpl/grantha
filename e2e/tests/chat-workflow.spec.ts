/**
 * Chat Workflow E2E Tests
 * Tests for chat functionality and user interactions
 */

import { test, expect } from '@playwright/test';

test.describe('Chat Workflow Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/chat');
    
    // Wait for chat interface to load
    await expect(page.locator('[data-testid="chat-area"]')).toBeVisible();
  });

  test('should display chat interface correctly', async ({ page }) => {
    // Check main chat components are visible
    await expect(page.locator('[data-testid="chat-sidebar"]')).toBeVisible();
    await expect(page.locator('[data-testid="chat-area"]')).toBeVisible();
    await expect(page.locator('[data-testid="chat-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="model-selector"]')).toBeVisible();
  });

  test('should send a chat message', async ({ page }) => {
    const testMessage = 'Hello, this is a test message';
    
    // Type message in input
    await page.fill('[data-testid="chat-input"]', testMessage);
    
    // Send message (Enter key or send button)
    await page.press('[data-testid="chat-input"]', 'Enter');
    
    // Check that message appears in chat area
    await expect(page.locator('[data-testid="chat-message"]').last()).toContainText(testMessage);
    
    // Input should be cleared
    await expect(page.locator('[data-testid="chat-input"]')).toHaveValue('');
  });

  test('should handle streaming responses', async ({ page }) => {
    const testMessage = 'What is artificial intelligence?';
    
    await page.fill('[data-testid="chat-input"]', testMessage);
    await page.press('[data-testid="chat-input"]', 'Enter');
    
    // Wait for response to start
    await expect(page.locator('[data-testid="typing-indicator"]')).toBeVisible();
    
    // Wait for response to complete (with timeout)
    await expect(page.locator('[data-testid="ai-response"]').last()).toBeVisible({ timeout: 30000 });
    
    // Check that response contains some content
    const response = page.locator('[data-testid="ai-response"]').last();
    await expect(response).not.toBeEmpty();
  });

  test('should create new conversation', async ({ page }) => {
    // Click new conversation button
    await page.click('[data-testid="new-conversation-btn"]');
    
    // Should clear current chat
    const messages = page.locator('[data-testid="chat-message"]');
    await expect(messages).toHaveCount(0);
    
    // Should show empty state or welcome message
    await expect(page.locator('[data-testid="empty-chat-state"]')).toBeVisible();
  });

  test('should switch between conversations', async ({ page }) => {
    // Send a message to create first conversation
    await page.fill('[data-testid="chat-input"]', 'First conversation');
    await page.press('[data-testid="chat-input"]', 'Enter');
    
    // Wait for message to appear
    await expect(page.locator('[data-testid="chat-message"]')).toHaveCount(1);
    
    // Create new conversation
    await page.click('[data-testid="new-conversation-btn"]');
    
    // Send message in new conversation
    await page.fill('[data-testid="chat-input"]', 'Second conversation');
    await page.press('[data-testid="chat-input"]', 'Enter');
    
    // Check sidebar shows both conversations
    const conversations = page.locator('[data-testid="conversation-item"]');
    await expect(conversations).toHaveCount(2);
    
    // Click on first conversation
    await conversations.first().click();
    
    // Should see first conversation's message
    await expect(page.locator('[data-testid="chat-message"]')).toContainText('First conversation');
  });

  test('should handle model selection', async ({ page }) => {
    // Open model selector
    await page.click('[data-testid="model-selector"]');
    
    // Check dropdown/modal appears
    await expect(page.locator('[data-testid="model-options"]')).toBeVisible();
    
    // Select a different model
    const modelOptions = page.locator('[data-testid="model-option"]');
    if (await modelOptions.count() > 1) {
      await modelOptions.nth(1).click();
      
      // Check that selection is updated
      const selectedModel = await page.locator('[data-testid="selected-model"]').textContent();
      expect(selectedModel).toBeTruthy();
    }
  });

  test('should handle error states', async ({ page }) => {
    // Mock network error
    await page.route('**/api/v1/chat**', route => {
      route.abort();
    });
    
    // Try to send message
    await page.fill('[data-testid="chat-input"]', 'This should fail');
    await page.press('[data-testid="chat-input"]', 'Enter');
    
    // Should show error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    
    // Should have retry option
    await expect(page.locator('[data-testid="retry-btn"]')).toBeVisible();
  });

  test('should support message actions', async ({ page }) => {
    // Send a message first
    await page.fill('[data-testid="chat-input"]', 'Test message for actions');
    await page.press('[data-testid="chat-input"]', 'Enter');
    
    // Wait for AI response
    await expect(page.locator('[data-testid="ai-response"]').last()).toBeVisible({ timeout: 30000 });
    
    // Hover over message to show actions
    const lastMessage = page.locator('[data-testid="ai-response"]').last();
    await lastMessage.hover();
    
    // Check copy button appears
    const copyBtn = page.locator('[data-testid="copy-message-btn"]').last();
    await expect(copyBtn).toBeVisible();
    
    // Click copy button
    await copyBtn.click();
    
    // Should show copy confirmation
    await expect(page.locator('[data-testid="copy-success"]')).toBeVisible();
  });

  test('should handle long conversations', async ({ page }) => {
    // Send multiple messages to test scrolling
    for (let i = 1; i <= 5; i++) {
      await page.fill('[data-testid="chat-input"]', `Message ${i}`);
      await page.press('[data-testid="chat-input"]', 'Enter');
      
      // Wait a bit between messages
      await page.waitForTimeout(1000);
    }
    
    // Check that all messages are present
    const messages = page.locator('[data-testid="chat-message"]');
    await expect(messages).toHaveCount(5);
    
    // Check that newest message is visible (auto-scroll)
    const lastMessage = messages.last();
    await expect(lastMessage).toBeInViewport();
  });
});
/**
 * Rate limit helper utilities for Playwright tests
 *
 * Respects backend rate limits:
 * - 60 requests per minute per IP
 * - 5 violations before 24-hour auto-ban
 */

export class RateLimitManager {
  private static requests: number = 0;
  private static windowStart: number = Date.now();
  private static readonly RATE_LIMIT = 50; // Stay under 60 req/min limit
  private static readonly WINDOW_MS = 60 * 1000; // 1 minute
  private static readonly MIN_DELAY = 1200; // 1.2s minimum between requests

  /**
   * Wait if needed to respect rate limits
   */
  static async throttle(): Promise<void> {
    const now = Date.now();

    // Reset window if 1 minute has passed
    if (now - this.windowStart >= this.WINDOW_MS) {
      this.requests = 0;
      this.windowStart = now;
    }

    // If we're approaching the limit, wait
    if (this.requests >= this.RATE_LIMIT) {
      const waitTime = this.WINDOW_MS - (now - this.windowStart) + 1000;
      console.log(`[RateLimit] Waiting ${Math.ceil(waitTime / 1000)}s for rate limit window reset`);
      await new Promise(resolve => setTimeout(resolve, waitTime));

      // Reset after waiting
      this.requests = 0;
      this.windowStart = Date.now();
    }

    this.requests++;

    // Add minimum delay between requests
    await new Promise(resolve => setTimeout(resolve, this.MIN_DELAY));
  }

  /**
   * Handle 429 responses with exponential backoff
   */
  static async handleRateLimit(retryAttempt: number = 1): Promise<void> {
    const baseDelay = 5000; // 5 seconds base
    const backoffMultiplier = Math.pow(2, retryAttempt - 1);
    const jitter = Math.random() * 1000; // Add jitter
    const totalDelay = baseDelay * backoffMultiplier + jitter;

    console.log(`[RateLimit] 429 received, backing off for ${Math.ceil(totalDelay / 1000)}s (attempt ${retryAttempt})`);
    await new Promise(resolve => setTimeout(resolve, totalDelay));
  }

  /**
   * Get current request count in window
   */
  static getRequestCount(): number {
    return this.requests;
  }

  /**
   * Get remaining requests in current window
   */
  static getRemainingRequests(): number {
    return Math.max(0, this.RATE_LIMIT - this.requests);
  }
}

/**
 * Retry wrapper with rate limit handling
 */
export async function withRateLimitRetry<T>(
  operation: () => Promise<T>,
  maxRetries: number = 3,
  context: string = 'operation'
): Promise<T> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      // Throttle before each attempt
      await RateLimitManager.throttle();

      const result = await operation();

      if (attempt > 1) {
        console.log(`[RateLimit] ${context} succeeded on attempt ${attempt}`);
      }

      return result;

    } catch (error: any) {
      // Check if this is a rate limit error
      if (error.message?.includes('429') ||
          error.message?.includes('Too many requests') ||
          error.message?.includes('Rate limit')) {

        if (attempt < maxRetries) {
          console.log(`[RateLimit] ${context} hit rate limit, attempt ${attempt}/${maxRetries}`);
          await RateLimitManager.handleRateLimit(attempt);
          continue;
        }
      }

      // For other errors or final attempt, re-throw
      throw error;
    }
  }

  throw new Error(`${context} failed after ${maxRetries} attempts`);
}
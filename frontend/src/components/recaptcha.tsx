'use client';

import { useEffect, useRef, useCallback, memo, useImperativeHandle, forwardRef } from 'react';

interface ReCaptchaProps {
  siteKey: string;
  onVerify: (token: string) => void;
  onExpire?: () => void;
  onError?: () => void;
  theme?: 'light' | 'dark';
  size?: 'normal' | 'compact';
}

export interface ReCaptchaRef {
  reset: () => void;
  execute: () => void;
  getResponse: () => string;
}

declare global {
  interface Window {
    grecaptcha: {
      ready: (callback: () => void) => void;
      render: (
        container: HTMLElement | string,
        parameters: {
          sitekey: string;
          callback?: (token: string) => void;
          'expired-callback'?: () => void;
          'error-callback'?: () => void;
          theme?: 'light' | 'dark';
          size?: 'normal' | 'compact';
        }
      ) => number;
      reset: (widgetId?: number) => void;
      execute: (widgetId?: number) => void;
      getResponse: (widgetId?: number) => string;
    };
  }
}

const ReCaptchaComponent = forwardRef<ReCaptchaRef, ReCaptchaProps>(({
  siteKey,
  onVerify,
  onExpire,
  onError,
  theme = 'light',
  size = 'normal',
}, ref) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetIdRef = useRef<number | null>(null);
  const callbacksRef = useRef({ onVerify, onExpire, onError });

  // Update callbacks ref without triggering re-render
  useEffect(() => {
    callbacksRef.current = { onVerify, onExpire, onError };
  }, [onVerify, onExpire, onError]);

  // Expose reset, execute, and getResponse methods via ref
  useImperativeHandle(ref, () => ({
    reset: () => {
      if (widgetIdRef.current !== null && window.grecaptcha) {
        window.grecaptcha.reset(widgetIdRef.current);
      }
    },
    execute: () => {
      if (widgetIdRef.current !== null && window.grecaptcha) {
        window.grecaptcha.execute(widgetIdRef.current);
      }
    },
    getResponse: () => {
      if (widgetIdRef.current !== null && window.grecaptcha) {
        return window.grecaptcha.getResponse(widgetIdRef.current);
      }
      return '';
    },
  }), []);

  // Stable callback functions that use the ref
  const handleVerify = useCallback((token: string) => {
    callbacksRef.current.onVerify(token);
  }, []);

  const handleExpire = useCallback(() => {
    callbacksRef.current.onExpire?.();
  }, []);

  const handleError = useCallback(() => {
    callbacksRef.current.onError?.();
  }, []);

  useEffect(() => {
    // Skip if already rendered
    if (widgetIdRef.current !== null) {
      return;
    }

    // Load reCAPTCHA script if not already loaded
    if (!document.getElementById('recaptcha-script')) {
      const script = document.createElement('script');
      script.id = 'recaptcha-script';
      script.src = 'https://www.google.com/recaptcha/api.js?render=explicit';
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);
    }

    // Wait for grecaptcha to be ready
    const checkRecaptcha = setInterval(() => {
      if (window.grecaptcha && window.grecaptcha.ready) {
        clearInterval(checkRecaptcha);

        window.grecaptcha.ready(() => {
          if (containerRef.current && widgetIdRef.current === null) {
            widgetIdRef.current = window.grecaptcha.render(containerRef.current, {
              sitekey: siteKey,
              callback: handleVerify,
              'expired-callback': handleExpire,
              'error-callback': handleError,
              theme,
              size,
            });
          }
        });
      }
    }, 100);

    // Cleanup
    return () => {
      clearInterval(checkRecaptcha);
    };
  }, [siteKey, handleVerify, handleExpire, handleError, theme, size]);

  // Skip rendering if no site key
  if (!siteKey) {
    return null;
  }

  return <div ref={containerRef} className="flex justify-center" />;
});

ReCaptchaComponent.displayName = 'ReCaptcha';

// Memoize the component to prevent unnecessary re-renders
export const ReCaptcha = memo(ReCaptchaComponent);

export function useReCaptcha() {
  const reset = useCallback((widgetId?: number) => {
    if (window.grecaptcha) {
      window.grecaptcha.reset(widgetId);
    }
  }, []);

  const execute = useCallback((widgetId?: number) => {
    if (window.grecaptcha) {
      window.grecaptcha.execute(widgetId);
    }
  }, []);

  const getResponse = useCallback((widgetId?: number) => {
    if (window.grecaptcha) {
      return window.grecaptcha.getResponse(widgetId);
    }
    return '';
  }, []);

  return { reset, execute, getResponse };
}

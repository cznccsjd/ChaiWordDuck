'use client';

import React from 'react';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from './index';

interface ReactQueryProviderProps {
  children: React.ReactNode;
  client?: QueryClient;
}

export function ReactQueryProvider({
  children,
  client = queryClient
}: ReactQueryProviderProps) {
  return (
    <QueryClientProvider client={client}>
      {children}
      {/* 开发环境下显示 Devtools */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools
          initialIsOpen={false}
          position="bottom"
        />
      )}
    </QueryClientProvider>
  );
}
/**
 * 数据加载 Hook
 * 
 * 自动加载 public/latest_report.json 文件
 */

import { useState, useEffect } from 'react';
import type { StrategyData } from '../types/data';
import { parseStrategyData } from '../utils/dataParser';

interface UseDataLoaderResult {
  data: StrategyData | null;
  loading: boolean;
  error: string | null;
}

export function useDataLoader(): UseDataLoaderResult {
  const [data, setData] = useState<StrategyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 自动加载 public/latest_report.json
  useEffect(() => {
    const loadLatestReport = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // 直接加载 public/latest_report.json（Vite 会自动处理 public 目录）
        const response = await fetch('/latest_report.json');
        if (!response.ok) {
          throw new Error(`无法加载数据文件: ${response.status} ${response.statusText}`);
        }
        const jsonData = await response.json();
        const parsedData = parseStrategyData(jsonData);
        setData(parsedData);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '加载数据失败';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    loadLatestReport();
  }, []);

  return {
    data,
    loading,
    error,
  };
}


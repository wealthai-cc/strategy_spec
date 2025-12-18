/**
 * 数据加载 Hook
 * 
 * 支持多种数据加载方式：
 * - URL 参数加载
 * - 文件上传
 * - HTTP API
 */

import { useState, useEffect } from 'react';
import type { StrategyData } from '../types/data';
import { parseStrategyData } from '../utils/dataParser';

interface UseDataLoaderResult {
  data: StrategyData | null;
  loading: boolean;
  error: string | null;
  loadFromFile: (file: File) => Promise<void>;
  loadFromUrl: (url: string) => Promise<void>;
}

export function useDataLoader(): UseDataLoaderResult {
  const [data, setData] = useState<StrategyData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadFromUrl = async (url: string) => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('正在加载数据 URL:', url);
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
      }
      const jsonData = await response.json();
      console.log('数据加载成功:', jsonData);
      const parsedData = parseStrategyData(jsonData);
      setData(parsedData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load from URL';
      console.error('数据加载失败:', err);
      setError(`${errorMessage}\nURL: ${url}`);
    } finally {
      setLoading(false);
    }
  };

  // 从 URL 参数加载数据
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const dataUrl = urlParams.get('data');
    
    if (dataUrl) {
      loadFromUrl(dataUrl);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadFromFile = async (file: File) => {
    setLoading(true);
    setError(null);
    
    try {
      const text = await file.text();
      const jsonData = JSON.parse(text);
      const parsedData = parseStrategyData(jsonData);
      setData(parsedData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load file');
    } finally {
      setLoading(false);
    }
  };

  return {
    data,
    loading,
    error,
    loadFromFile,
    loadFromUrl,
  };
}


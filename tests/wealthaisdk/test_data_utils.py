"""
WealthAI SDK 数据工具测试
"""

import unittest
import pandas as pd

from wealthai_sdk import bars_to_dataframe


class TestDataUtils(unittest.TestCase):
    """数据工具测试类"""
    
    def test_bars_to_dataframe_with_objects(self):
        """测试 Bar 对象转 DataFrame"""
        
        class MockBar:
            def __init__(self, open_price, high, low, close, volume, close_time):
                self.open = open_price
                self.high = high
                self.low = low
                self.close = close
                self.volume = volume
                self.close_time = close_time
        
        bars = [
            MockBar(100.0, 105.0, 95.0, 102.0, 1000.0, 1640995200),
            MockBar(102.0, 108.0, 98.0, 105.0, 1200.0, 1640998800),
            MockBar(105.0, 110.0, 100.0, 107.0, 1100.0, 1641002400)
        ]
        
        df = bars_to_dataframe(bars)
        
        # 检查 DataFrame 结构
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)
        self.assertEqual(list(df.columns), ['open', 'high', 'low', 'close', 'volume'])
        self.assertEqual(df.index.name, 'close_time')
        
        # 检查数据类型
        self.assertTrue(all(df.dtypes == 'float64'))
        
        # 检查具体数据
        self.assertEqual(df.iloc[0]['open'], 100.0)
        self.assertEqual(df.iloc[0]['close'], 102.0)
        self.assertEqual(df.iloc[1]['close'], 105.0)
        self.assertEqual(df.iloc[2]['high'], 110.0)
        
        # 检查索引
        self.assertEqual(df.index[0], 1640995200)
        self.assertEqual(df.index[1], 1640998800)
    
    def test_bars_to_dataframe_with_dicts(self):
        """测试字典格式的 Bar 转 DataFrame"""
        bars = [
            {
                'open': 100.0,
                'high': 105.0,
                'low': 95.0,
                'close': 102.0,
                'volume': 1000.0,
                'close_time': 1640995200
            },
            {
                'open': 102.0,
                'high': 108.0,
                'low': 98.0,
                'close': 105.0,
                'volume': 1200.0,
                'close_time': 1640998800
            }
        ]
        
        df = bars_to_dataframe(bars)
        
        # 检查 DataFrame 结构
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns), ['open', 'high', 'low', 'close', 'volume'])
        
        # 检查数据
        self.assertEqual(df.iloc[0]['open'], 100.0)
        self.assertEqual(df.iloc[1]['volume'], 1200.0)
    
    def test_bars_to_dataframe_empty(self):
        """测试空 Bar 列表"""
        df = bars_to_dataframe([])
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 0)
        self.assertEqual(list(df.columns), ['open', 'high', 'low', 'close', 'volume'])
    
    def test_bars_to_dataframe_single_bar(self):
        """测试单个 Bar 的转换"""
        class MockBar:
            def __init__(self, open_price, high, low, close, volume, close_time):
                self.open = open_price
                self.high = high
                self.low = low
                self.close = close
                self.volume = volume
                self.close_time = close_time
        
        bars = [MockBar(42000.0, 42500.0, 41500.0, 42200.0, 1000.0, 1640995200)]
        
        df = bars_to_dataframe(bars)
        
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['open'], 42000.0)
        self.assertEqual(df.iloc[0]['close'], 42200.0)
    
    def test_bars_to_dataframe_mixed_types(self):
        """测试混合类型的数值转换"""
        bars = [
            {
                'open': 100,      # int
                'high': 105.5,    # float
                'low': '95.0',    # string (should be converted)
                'close': 102.0,   # float
                'volume': 1000,   # int
                'close_time': 1640995200
            }
        ]
        
        df = bars_to_dataframe(bars)
        
        # 检查所有数值列都被转换为 float
        self.assertTrue(all(df.dtypes == 'float64'))
        self.assertEqual(df.iloc[0]['low'], 95.0)
    
    def test_bars_to_dataframe_invalid_format(self):
        """测试无效格式的 Bar 对象"""
        invalid_bars = ["not_a_bar_object", 123, None]
        
        with self.assertRaises(ValueError) as context:
            bars_to_dataframe(invalid_bars)
        
        self.assertIn("不支持的 Bar 对象类型", str(context.exception))
    
    def test_bars_to_dataframe_missing_fields(self):
        """测试缺少必需字段的 Bar 对象"""
        incomplete_bars = [
            {
                'open': 100.0,
                'high': 105.0,
                # 缺少 'low', 'close', 'volume', 'close_time'
            }
        ]
        
        with self.assertRaises(KeyError):
            bars_to_dataframe(incomplete_bars)
    
    def test_bars_to_dataframe_pandas_operations(self):
        """测试转换后的 DataFrame 支持 pandas 操作"""
        class MockBar:
            def __init__(self, open_price, high, low, close, volume, close_time):
                self.open = open_price
                self.high = high
                self.low = low
                self.close = close
                self.volume = volume
                self.close_time = close_time
        
        bars = [
            MockBar(100.0, 105.0, 95.0, 102.0, 1000.0, 1640995200),
            MockBar(102.0, 108.0, 98.0, 105.0, 1200.0, 1640998800),
            MockBar(105.0, 110.0, 100.0, 107.0, 1100.0, 1641002400)
        ]
        
        df = bars_to_dataframe(bars)
        
        # 测试常用的 pandas 操作
        mean_close = df['close'].mean()
        self.assertAlmostEqual(mean_close, 104.666667, places=5)
        
        max_high = df['high'].max()
        self.assertEqual(max_high, 110.0)
        
        min_low = df['low'].min()
        self.assertEqual(min_low, 95.0)
        
        total_volume = df['volume'].sum()
        self.assertEqual(total_volume, 3300.0)
        
        # 测试索引操作
        self.assertEqual(len(df.index), 3)
        self.assertTrue(df.index.is_monotonic_increasing)


if __name__ == '__main__':
    unittest.main()
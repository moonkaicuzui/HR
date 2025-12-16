#!/usr/bin/env python3
"""
추세선 계산 테스트
Test the trend line calculation with sample data
"""

import numpy as np
import matplotlib.pyplot as plt

def calculate_trend_line_python(data):
    """
    Python implementation of the JavaScript calculateTrendLine function
    to verify the calculation logic
    """
    n = len(data)
    if n < 2:
        return data

    # Calculate means
    x_mean = (n - 1) / 2
    y_mean = sum(data) / n

    # Calculate slope and intercept
    numerator = 0
    denominator = 0

    for i in range(n):
        numerator += (i - x_mean) * (data[i] - y_mean)
        denominator += (i - x_mean) * (i - x_mean)

    slope = numerator / denominator if denominator != 0 else 0
    intercept = y_mean - slope * x_mean

    # Generate trend line data
    trend_data = []
    for i in range(n):
        trend_data.append(intercept + slope * i)

    return trend_data

def test_trend_calculation():
    """Test trend line calculation with sample data"""

    print("=" * 80)
    print("추세선 계산 테스트 (Trend Line Calculation Test)")
    print("=" * 80)

    # Sample data representing daily absence rates over 30 days
    # Simulating a gradual decrease in absence rate (improvement trend)
    np.random.seed(42)
    days = 30
    base_rate = 3.5
    trend_decrease = -0.05  # Decrease of 0.05% per day

    # Generate sample data with some noise
    sample_data = []
    for i in range(days):
        rate = base_rate + (trend_decrease * i) + np.random.normal(0, 0.3)
        sample_data.append(max(0, rate))  # Ensure non-negative

    print(f"\n📊 테스트 데이터:")
    print(f"   - 일수: {days}일")
    print(f"   - 시작 결근율: {sample_data[0]:.2f}%")
    print(f"   - 종료 결근율: {sample_data[-1]:.2f}%")
    print(f"   - 평균 결근율: {np.mean(sample_data):.2f}%")

    # Calculate trend line
    trend_line = calculate_trend_line_python(sample_data)

    print(f"\n📈 추세선 분석:")
    print(f"   - 추세선 시작값: {trend_line[0]:.2f}%")
    print(f"   - 추세선 종료값: {trend_line[-1]:.2f}%")

    # Calculate trend direction
    trend_change = trend_line[-1] - trend_line[0]
    if trend_change < 0:
        print(f"   - 추세: ⬇️ 감소 추세 ({trend_change:.2f}% 감소)")
    elif trend_change > 0:
        print(f"   - 추세: ⬆️ 증가 추세 ({trend_change:.2f}% 증가)")
    else:
        print(f"   - 추세: ➡️ 변화 없음")

    # Verify the calculation matches numpy's linear regression
    x = np.arange(days)
    coefficients = np.polyfit(x, sample_data, 1)  # Linear fit
    numpy_trend = np.poly1d(coefficients)(x)

    print(f"\n✅ 검증:")
    print(f"   - 계산된 추세선 첫 값: {trend_line[0]:.4f}")
    print(f"   - NumPy 추세선 첫 값: {numpy_trend[0]:.4f}")
    print(f"   - 차이: {abs(trend_line[0] - numpy_trend[0]):.6f}")

    # Check if our calculation matches NumPy's (within floating point precision)
    is_accurate = np.allclose(trend_line, numpy_trend, rtol=1e-5)
    if is_accurate:
        print("   ✓ 추세선 계산이 정확합니다!")
    else:
        print("   ✗ 추세선 계산에 오차가 있습니다.")

    # Create visualization
    plt.figure(figsize=(12, 6))
    plt.plot(x, sample_data, 'o-', label='실제 데이터', alpha=0.6, linewidth=1)
    plt.plot(x, trend_line, '--', label='추세선 (계산된)', linewidth=2, color='red')
    plt.plot(x, numpy_trend, ':', label='추세선 (NumPy)', linewidth=2, color='green')

    plt.xlabel('일 (Day)')
    plt.ylabel('결근율 (%)')
    plt.title('일별 결근율 및 추세선')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save plot
    plt.savefig('output_reports/trend_line_test.png', dpi=100)
    print(f"\n📊 시각화 저장: output_reports/trend_line_test.png")

    return is_accurate

if __name__ == "__main__":
    success = test_trend_calculation()
    print("\n" + "=" * 80)
    if success:
        print("🎉 추세선 계산 알고리즘이 정확하게 구현되었습니다!")
    else:
        print("⚠️  추세선 계산에 문제가 있을 수 있습니다.")
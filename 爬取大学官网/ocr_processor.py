"""
ocr_processor.py - OCR图像处理模块

本模块主要功能：
1. PaddleOCR引擎单例模式管理
   - 全局只初始化一次OCR引擎
   - 提供获取已初始化引擎的接口

2. PaddleOCR引擎初始化
   - 初始化PaddleOCR引擎（使用中文语言模型）
   - 配置角度分类、CPU模式

版本要求: Python3.9 / PaddleOCR2.7.0.3 / PaddlePaddle2.6.2 / NumPy1.26.4
"""

import os
import traceback

# 全局OCR引擎实例（单例模式）
_ocr_engine_instance = None
# OCR引擎是否已初始化标志
_ocr_initialized = False


def get_ocr_engine():
    """
    获取全局OCR引擎实例（单例模式）

    功能说明：
    - 返回全局已初始化的OCR引擎
    - 用于检查引擎是否已初始化

    返回值说明：
        tuple: (ocr_engine, initialized_flag)
            - ocr_engine: PaddleOCR引擎实例或None
            - initialized_flag: 是否已初始化的布尔值
    """
    global _ocr_engine_instance, _ocr_initialized
    return _ocr_engine_instance, _ocr_initialized


def init_paddleocr(force_reinit=False):
    """
    初始化PaddleOCR引擎（单例模式，全局只初始化一次）

    功能说明：
    - 使用单例模式确保全局只有一个OCR引擎实例
    - 首次调用时初始化引擎，后续调用返回已初始化的引擎
    - 支持强制重新初始化（force_reinit=True）

    参数说明：
        force_reinit: 是否强制重新初始化，默认False

    返回值说明：
        PaddleOCR引擎实例或None（初始化失败时）

    配置说明：
        - use_angle_cls: True 使用角度分类器，提高识别准确率
        - lang: 'ch' 使用中文语言模型
        - use_gpu: False 使用CPU模式（避免GPU资源占用）
    """
    global _ocr_engine_instance, _ocr_initialized

    # 如果已初始化且不需要强制重新初始化，直接返回已初始化的引擎
    if _ocr_initialized and _ocr_engine_instance is not None and not force_reinit:
        return _ocr_engine_instance

    try:
        from paddleocr import PaddleOCR

        # 初始化PaddleOCR引擎
        _ocr_engine_instance = PaddleOCR(
            use_angle_cls=True,
            lang='ch',
            use_gpu=False
        )
        _ocr_initialized = True
        return _ocr_engine_instance

    except ImportError as e:
        print(f"[OCR] 导入PaddleOCR失败: {e}")
        print("[OCR] 解决方案: pip install paddleocr==2.7.0.3")
        traceback.print_exc()
        return None

    except OSError as e:
        print(f"[OCR] 模型文件读取失败: {e}")
        print("[OCR] 解决方案: 重新下载PaddleOCR模型或检查安装")
        traceback.print_exc()
        return None

    except Exception as e:
        print(f"[OCR] 初始化失败: {e}")
        print(f"[OCR] 详细错误: {traceback.format_exc()}")
        return None


if __name__ == '__main__':
    print("=" * 60)
    print("PaddleOCR 单例初始化测试")
    print("=" * 60)

    print("\n首次初始化...")
    engine1 = init_paddleocr()
    if engine1:
        print("首次初始化成功")
    else:
        print("首次初始化失败")

    print("\n再次获取（应返回缓存实例）...")
    engine2 = init_paddleocr()
    if engine1 is engine2:
        print("单例模式正常：两次获取的是同一实例")
    else:
        print("单例模式异常：获取了不同实例")

    print("\n" + "=" * 60)

import os
from PIL import Image

def crop_thumbnail_to_square(base_filename: str, cover_dir: str):
    """查找原始图片，生成正方形的 jpg 版本，并保留原图"""
    valid_exts = ['.webp', '.jpg', '.jpeg', '.png']
    original_img_path = None
    
    # 在专属的 covers 目录中寻找下载好的原图
    for ext in valid_exts:
        potential_path = os.path.join(cover_dir, f"{base_filename}{ext}")
        if os.path.exists(potential_path):
            original_img_path = potential_path
            break

    if not original_img_path:
        print(f"未找到原始缩略图: {base_filename}")
        return

    try:
        with Image.open(original_img_path) as img:
            width, height = img.size
            # 输出的正方形图片也在 covers 目录中
            out_path = os.path.join(cover_dir, f"{base_filename}_square.jpg")

            # 如果原图已经是正方形
            if width == height:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(out_path, "JPEG", quality=95)
                print(f"原图已是正方形，已生成 Yoto 兼容副本: {out_path}")
                return

            # 计算居中裁剪的坐标
            new_size = min(width, height)
            left = (width - new_size) / 2
            top = (height - new_size) / 2
            right = (width + new_size) / 2
            bottom = (height + new_size) / 2

            img_cropped = img.crop((left, top, right, bottom))
            
            # 转换为 RGB 并保存
            if img_cropped.mode in ("RGBA", "P"):
                img_cropped = img_cropped.convert("RGB")
            
            img_cropped.save(out_path, "JPEG", quality=95)
            print(f"原图保留，已生成正方形裁剪版: {out_path}")
            
    except Exception as e:
        print(f"处理图片时出错: {e}")
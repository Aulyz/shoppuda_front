import os
import re
import unicodedata
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
import markdown
from markdown.extensions.toc import TocExtension


# ===== 권한 체크 =====
def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser or getattr(user, "admin_level", 0) >= 3)

def secure_filename(filename):
    if any(x in filename for x in ("..", "/", "\\")):
        raise Http404("잘못된 파일명입니다.")
    return filename

# ===== 한글 지원 slugify =====
def slugify_kr(value, separator="-"):
    value = unicodedata.normalize("NFKC", value)
    value = value.strip()
    value = re.sub(r"\s+", separator, value)
    value = re.sub(rf"[^\w가-힣\-{separator}]", "", value, flags=re.UNICODE)
    value = re.sub(rf"{separator}+", separator, value)
    return value.lower()


# ===== 목차 토큰 평탄화 =====
def flatten_toc(tokens, acc=None):
    if acc is None:
        acc = []
    for t in tokens:
        acc.append({
            "level": int(t.get("level", 1)),
            "id": t.get("id", ""),
            "title": t.get("name", ""),
        })
        if t.get("children"):
            flatten_toc(t["children"], acc)
    return acc


# ===== 문서 상세 뷰 =====
@login_required
@user_passes_test(is_admin)
def documentation_view(request, filename):
    # 보안: 경로 탐색 방지
    if any(x in filename for x in ("..", "/", "\\")):
        raise Http404("잘못된 파일명입니다.")

    if not filename.endswith(".md"):
        filename += ".md"

    docs_dir = os.path.join(settings.BASE_DIR, "문서")
    file_path = os.path.join(docs_dir, filename)

    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise Http404("문서를 찾을 수 없습니다.")

    with open(file_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # 마크다운 변환기
    md_converter = markdown.Markdown(
        extensions=[
            TocExtension(slugify=slugify_kr, permalink=True, toc_depth="1-6"),
            "extra",        # 표, 목록 등 확장 지원
            "fenced_code",  # ``` 코드 블록
            "tables",       # 표 지원
            "codehilite",   # 코드 하이라이트
            "attr_list",    # {} 속성 지원
            "sane_lists",   # 깔끔한 리스트 처리
            "nl2br",        # 한 줄 개행 -> <br>
        ],
        extension_configs={
            "codehilite": {"guess_lang": False, "noclasses": False}
        },
    )
    html_content = md_converter.convert(md_text)
    toc_items = flatten_toc(getattr(md_converter, "toc_tokens", []))

    context = {
        "filename": filename,
        "title": filename.replace(".md", "").replace("_", " "),
        "content": html_content,   # HTML 변환된 것
        "toc_items": toc_items,    # 템플릿에서 JS가 목차 생성
    }

    if request.GET.get("format") == "raw":
        return HttpResponse(md_text, content_type="text/plain; charset=utf-8")

    return render(request, "core/documentation_view.html", context)

# ===== 다운로드 =====
@login_required
@user_passes_test(is_admin)
def documentation_download(request, filename):
    """문서 다운로드"""
    filename = secure_filename(filename)

    if not filename.endswith(".md"):
        filename += ".md"

    docs_dir = os.path.join(settings.BASE_DIR, "문서")
    file_path = os.path.join(docs_dir, filename)

    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise Http404("문서를 찾을 수 없습니다.")

    try:
        with open(file_path, "rb") as f:
            response = HttpResponse(f.read(), content_type="text/markdown; charset=utf-8")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
    except Exception as e:
        raise Http404(f"문서를 다운로드할 수 없습니다: {e}")

# ===== 목록 =====
@login_required
@user_passes_test(is_admin)
def documentation_list(request):
    """문서 목록 보기"""
    docs_dir = os.path.join(settings.BASE_DIR, "문서")

    if not os.path.exists(docs_dir):
        raise Http404("문서 디렉토리가 존재하지 않습니다.")

    documents = []
    for filename in os.listdir(docs_dir):
        if filename.endswith(".md"):
            file_path = os.path.join(docs_dir, filename)
            file_size = os.path.getsize(file_path) / 1024  # KB
            file_mtime = os.path.getmtime(file_path)
            documents.append(
                {
                    "name": filename,
                    "title": filename.replace(".md", "").replace("_", " "),
                    "size": f"{file_size:.1f} KB",
                    "modified": file_mtime,
                }
            )

    documents.sort(key=lambda x: x["modified"], reverse=True)

    context = {"documents": documents, "page_title": "프로젝트 문서"}
    return render(request, "core/documentation_list.html", context)
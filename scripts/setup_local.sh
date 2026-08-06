#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$PROJECT_DIR"

CONDA_ENV_NAME="${SHINSEKAI_CONDA_ENV:-shinsekai}"
VENV_DIR="$PROJECT_DIR/.venv"
PYTHON_CMD=()

say() {
    printf '\n==> %s\n' "$1"
}

find_conda() {
    if [ -n "${CONDA_EXE:-}" ] && [ -x "$CONDA_EXE" ]; then
        printf '%s\n' "$CONDA_EXE"
        return 0
    fi
    if command -v conda >/dev/null 2>&1; then
        command -v conda
        return 0
    fi
    for candidate in "$HOME/miniconda3/bin/conda" "$HOME/anaconda3/bin/conda" \
        "/opt/miniconda3/bin/conda" "/opt/anaconda3/bin/conda"; do
        if [ -x "$candidate" ]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    return 1
}

conda_env_exists() {
    "$1" env list 2>/dev/null | awk '{print $1}' | grep -qx "$CONDA_ENV_NAME"
}

say "检查 Python 环境"
if [ -x "$VENV_DIR/bin/python" ]; then
    PYTHON_CMD=("$VENV_DIR/bin/python")
    echo "使用项目环境: .venv"
else
    CONDA_CMD=""
    if [ "${SHINSEKAI_USE_CONDA:-0}" = "1" ] && CONDA_CMD="$(find_conda)" && conda_env_exists "$CONDA_CMD"; then
        PYTHON_CMD=("$CONDA_CMD" run -n "$CONDA_ENV_NAME" python)
        echo "使用 Conda 环境: $CONDA_ENV_NAME"
    elif [ "${SHINSEKAI_USE_CONDA:-0}" = "1" ] && CONDA_CMD="$(find_conda)"; then
        echo "正在创建 Conda 环境: $CONDA_ENV_NAME"
        if "$CONDA_CMD" env create -f environment.yml \
            --override-channels \
            -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge \
            -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main; then
            PYTHON_CMD=("$CONDA_CMD" run -n "$CONDA_ENV_NAME" python)
            echo "Conda 环境创建完成"
        else
            echo "Conda 下载失败，自动改用项目内 .venv"
        fi
    fi

    if [ "${#PYTHON_CMD[@]}" -eq 0 ]; then
        if ! command -v python3 >/dev/null 2>&1; then
            echo "错误：找不到 Python 3。请先安装 Python 3.10 或更高版本。"
            exit 1
        fi
        say "创建项目内 Python 环境"
        python3 -m venv "$VENV_DIR"
        PYTHON_CMD=("$VENV_DIR/bin/python")
        "${PYTHON_CMD[@]}" -m pip install --upgrade pip
        "${PYTHON_CMD[@]}" -m pip install -r requirements.txt \
            -i https://pypi.tuna.tsinghua.edu.cn/simple
    fi
fi

say "检查前端"
if ! command -v pnpm >/dev/null 2>&1; then
    if command -v corepack >/dev/null 2>&1; then
        corepack enable pnpm >/dev/null 2>&1 || true
    fi
fi
if ! command -v pnpm >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    echo "未找到 pnpm，正在从镜像自动安装..."
    corepack disable >/dev/null 2>&1 || true
    npm install --global pnpm@latest-11 --registry=https://registry.npmmirror.com
fi
if ! command -v pnpm >/dev/null 2>&1; then
    echo "错误：找不到 pnpm。请确认 Node.js 已安装后重新运行此脚本。"
    exit 1
fi
cd frontend
if [ ! -d node_modules ]; then
    pnpm install --registry=https://registry.npmmirror.com
fi
pnpm build
cd "$PROJECT_DIR"

say "同步四宫辉夜配置"
"${PYTHON_CMD[@]}" scripts/setup_shinomiya_defaults.py

say "设置完成"
echo "以后可以直接双击 start-react.command 启动。"

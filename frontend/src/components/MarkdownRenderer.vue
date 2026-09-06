<script setup lang="ts">
// 统一的 Markdown + KaTeX 渲染组件。对应文档 05 §4、§7。
// 负责渲染笔记/题目/卡片中的富文本与数学公式；渲染失败时降级显示原始文本。
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const props = defineProps<{ content: string }>()

function katexMath(src: string, display: boolean): string {
  try {
    return katex.renderToString(src, {
      displayMode: display,
      throwOnError: false,
      output: 'html',
    })
  } catch {
    return src
  }
}

// 自定义行内数学规则：$...$
function mathInline(state, silent: boolean): boolean {
  const start = state.pos
  const src = state.src
  if (src.charAt(start) !== '$') return false
  if (src.charAt(start + 1) === '$') return false // 块级交给 block 规则
  // 前一个字符不能是字母/数字（避免 $5$ 价格误判）
  if (start > 0 && /[\w0-9]/.test(src.charAt(start - 1))) return false
  let pos = start + 1
  let end = -1
  while (pos < src.length) {
    if (src.charAt(pos) === '$' && src.charAt(pos - 1) !== '\\') {
      end = pos
      break
    }
    pos++
  }
  if (end < 0) return false
  if (silent) return true
  const token = state.push('math_inline', 'math_inline', 0)
  token.content = src.slice(start + 1, end).trim()
  state.pos = end + 1
  return true
}

// 自定义块级数学规则：$$...$$
function mathBlock(state, startLine: number, endLine: number, silent: boolean): boolean {
  const start = state.bMarks[startLine] + state.tShift[startLine]
  const src = state.src
  if (src.charAt(start) !== '$' || src.charAt(start + 1) !== '$') return false
  // 找同行的闭合 $$ 或跨行
  let pos = start + 2
  let end = -1
  while (pos < src.length) {
    if (src.charAt(pos) === '$' && src.charAt(pos + 1) === '$') {
      end = pos
      break
    }
    pos++
  }
  if (end < 0) return false
  const content = src.slice(start + 2, end).trim()
  const nextLine = startLine + 1
  if (silent) return true
  const token = state.push('math_block', 'math_block', 0)
  token.content = content
  token.map = [startLine, nextLine]
  state.line = nextLine
  return true
}

const md = new MarkdownIt({ html: true, linkify: true, breaks: true })
md.inline.ruler.after('escape', 'math_inline', mathInline)
md.block.ruler.before('fence', 'math_block', mathBlock, { alt: ['paragraph', 'reference', 'blockquote', 'list'] })
md.renderer.rules.math_inline = (tokens, idx) => katexMath(tokens[idx].content, false)
md.renderer.rules.math_block = (tokens, idx) => `<div class="math-block">${katexMath(tokens[idx].content, true)}</div>`

const html = computed(() => {
  try {
    return md.render(props.content || '')
  } catch {
    return `<pre>${escapeHtml(props.content || '')}</pre>`
  }
})

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}
</script>

<template>
  <div class="md-renderer" v-html="html"></div>
</template>

<style>
.md-renderer .math-block {
  overflow-x: auto;
  margin: 0.6em 0;
}
.md-renderer pre {
  background: #f6f8fa;
  padding: 0.6em;
  border-radius: 6px;
  overflow-x: auto;
}
.md-renderer code {
  background: #f6f8fa;
  padding: 0.1em 0.3em;
  border-radius: 4px;
}
</style>

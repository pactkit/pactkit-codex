"""Tests for STORY-slim-046: FrontendParser — Hook & Store."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from pactkit.skills.visualize import (
    FrontendParser,
    WorkflowEdge,
    WorkflowGraph,
    WorkflowNode,
    _parse_hook_store_imports,
    _scan_hooks,
    _scan_stores,
)


def make_project(tmp_path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')
    return tmp_path


# --- AC1: Hook nodes from hooks directory ---

class TestScanHooks:
    def test_hook_node_from_hooks_dir(self, tmp_path):
        make_project(tmp_path, {
            'src/hooks/useAuth.ts': "export function useAuth() { return {} }",
        })
        graph = WorkflowGraph()
        _scan_hooks(tmp_path, graph)
        hook_nodes = [n for n in graph.nodes.values() if n.kind == 'hook']
        assert any(n.id == 'useAuth' for n in hook_nodes)

    def test_hook_node_from_composables_dir(self, tmp_path):
        make_project(tmp_path, {
            'composables/useI18n.ts': "export function useI18n() {}",
        })
        graph = WorkflowGraph()
        _scan_hooks(tmp_path, graph)
        hook_nodes = [n for n in graph.nodes.values() if n.kind == 'hook']
        assert any(n.id == 'useI18n' for n in hook_nodes)

    def test_src_composables_dir(self, tmp_path):
        make_project(tmp_path, {
            'src/composables/useCart.ts': "export function useCart() {}",
        })
        graph = WorkflowGraph()
        _scan_hooks(tmp_path, graph)
        hook_nodes = [n for n in graph.nodes.values() if n.kind == 'hook']
        assert any(n.id == 'useCart' for n in hook_nodes)

    def test_non_hook_file_ignored(self, tmp_path):
        make_project(tmp_path, {
            'src/hooks/utils.ts': "export function formatDate() {}",
        })
        graph = WorkflowGraph()
        _scan_hooks(tmp_path, graph)
        # utils.ts does NOT start with 'use' — not a hook
        hook_ids = [n.id for n in graph.nodes.values() if n.kind == 'hook']
        assert 'utils' not in hook_ids


# --- AC3: Store nodes ---

class TestScanStores:
    def test_store_node_from_store_dir(self, tmp_path):
        make_project(tmp_path, {
            'src/store/authSlice.ts': "import { createSlice } from '@reduxjs/toolkit'\nconst slice = createSlice({ name: 'auth' })",
        })
        graph = WorkflowGraph()
        _scan_stores(tmp_path, graph)
        store_nodes = [n for n in graph.nodes.values() if n.kind == 'store']
        assert any(n.id == 'authSlice' for n in store_nodes)

    def test_store_node_from_stores_dir(self, tmp_path):
        make_project(tmp_path, {
            'src/stores/cartStore.ts': "import { defineStore } from 'pinia'\nexport const cartStore = defineStore('cart', {})",
        })
        graph = WorkflowGraph()
        _scan_stores(tmp_path, graph)
        store_nodes = [n for n in graph.nodes.values() if n.kind == 'store']
        assert any(n.id == 'cartStore' for n in store_nodes)

    def test_zustand_store_detected(self, tmp_path):
        make_project(tmp_path, {
            'src/store/userStore.ts': "import { create } from 'zustand'\nexport const useUserStore = create((set) => ({}))",
        })
        graph = WorkflowGraph()
        _scan_stores(tmp_path, graph)
        store_nodes = [n for n in graph.nodes.values() if n.kind == 'store']
        assert any('userStore' in n.id for n in store_nodes)


# --- AC2: Component→hook edge (uses_hook) ---

class TestHookStoreImports:
    def test_component_uses_hook_edge(self, tmp_path):
        make_project(tmp_path, {
            'src/hooks/useAuth.ts': "export function useAuth() {}",
            'components/LoginForm.tsx': "import { useAuth } from '../hooks/useAuth'\nexport function LoginForm() {}",
        })
        graph = WorkflowGraph()
        graph.add_node(WorkflowNode(id='useAuth', kind='hook', label='useAuth'))
        graph.add_node(WorkflowNode(id='LoginForm', kind='component', label='LoginForm'))
        # Simulate importing useAuth from local path
        component_file = tmp_path / 'components/LoginForm.tsx'
        _parse_hook_store_imports([(None, 'LoginForm', component_file)], graph)
        edges = [(e.source, e.target, e.relation) for e in graph.edges]
        assert ('LoginForm', 'useAuth', 'uses_hook') in edges

    def test_hook_reads_store_edge(self, tmp_path):
        make_project(tmp_path, {
            'src/store/authSlice.ts': "export const authSlice = createSlice({})",
            'src/hooks/useAuth.ts': "import authSlice from '../store/authSlice'\nexport function useAuth() {}",
        })
        graph = WorkflowGraph()
        graph.add_node(WorkflowNode(id='useAuth', kind='hook', label='useAuth'))
        graph.add_node(WorkflowNode(id='authSlice', kind='store', label='authSlice'))
        hook_file = tmp_path / 'src/hooks/useAuth.ts'
        _parse_hook_store_imports([(None, 'useAuth', hook_file)], graph)
        edges = [(e.source, e.target, e.relation) for e in graph.edges]
        assert ('useAuth', 'authSlice', 'reads_store') in edges


# --- AC5: Full chain traversal ---

class TestFullChainTraversal:
    def test_reverse_reach_full_chain(self):
        """LoginPage → LoginForm → useAuth → authSlice chain is traversable."""
        graph = WorkflowGraph()
        graph.add_node(WorkflowNode(id='/login', kind='page', label='/login'))
        graph.add_node(WorkflowNode(id='LoginForm', kind='component', label='LoginForm'))
        graph.add_node(WorkflowNode(id='useAuth', kind='hook', label='useAuth'))
        graph.add_node(WorkflowNode(id='authSlice', kind='store', label='authSlice'))
        graph.add_edge(WorkflowEdge(source='/login', target='LoginForm', relation='renders'))
        graph.add_edge(WorkflowEdge(source='LoginForm', target='useAuth', relation='uses_hook'))
        graph.add_edge(WorkflowEdge(source='useAuth', target='authSlice', relation='reads_store'))

        reached = graph.reverse_reach('authSlice')
        assert 'useAuth' in reached
        assert 'LoginForm' in reached
        assert '/login' in reached

    def test_full_parse_creates_hook_store_nodes(self, tmp_path):
        """Integration: FrontendParser.parse() creates hook and store nodes."""
        make_project(tmp_path, {
            'next.config.js': '',
            'src/hooks/useAuth.ts': "export function useAuth() {}",
            'src/store/authSlice.ts': "import { createSlice } from '@reduxjs/toolkit'\nconst s = createSlice({ name: 'auth' })",
        })
        graph = FrontendParser().parse(tmp_path)
        kinds = {n.kind for n in graph.nodes.values()}
        assert 'hook' in kinds
        assert 'store' in kinds

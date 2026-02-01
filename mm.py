import os
import sys

# ─── Renkler (Terminal) ───────────────────────────────────────────
class Colors:
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

def clear():
    os.system("cls" if os.name == "nt" else "clear")

# ─── Node Sınıfı ──────────────────────────────────────────────────
class Node:
    def __init__(self, value):
        self.value = value
        self.left  = None
        self.right = None

# ─── BST Sınıfı ───────────────────────────────────────────────────
class BST:
    def __init__(self):
        self.root = None

    # ── Insert ────────────────────────────────────────────────────
    def insert(self, value):
        if self.root is None:
            self.root = Node(value)
            return True
        current = self.root
        while True:
            if value == current.value:
                return False  # duplicate
            elif value < current.value:
                if current.left is None:
                    current.left = Node(value)
                    return True
                current = current.left
            else:
                if current.right is None:
                    current.right = Node(value)
                    return True
                current = current.right

    # ── Search ────────────────────────────────────────────────────
    def search(self, value):
        path = []
        current = self.root
        while current:
            path.append(current.value)
            if value == current.value:
                return True, path
            elif value < current.value:
                current = current.left
            else:
                current = current.right
        return False, path

    # ── Delete ────────────────────────────────────────────────────
    def delete(self, value):
        self.root, deleted = self._delete_recursive(self.root, value)
        return deleted

    def _delete_recursive(self, node, value):
        if node is None:
            return None, False

        deleted = False
        if value < node.value:
            node.left, deleted = self._delete_recursive(node.left, value)
        elif value > node.value:
            node.right, deleted = self._delete_recursive(node.right, value)
        else:
            deleted = True
            # Case 1: Leaf node
            if node.left is None and node.right is None:
                return None, True
            # Case 2: Tek çocuk
            if node.left is None:
                return node.right, True
            if node.right is None:
                return node.left, True
            # Case 3: İki çocuk → inorder successor bul
            successor = self._find_min(node.right)
            node.value = successor.value
            node.right, _ = self._delete_recursive(node.right, successor.value)

        return node, deleted

    def _find_min(self, node):
        while node.left:
            node = node.left
        return node

    # ── Traversals ────────────────────────────────────────────────
    def inorder(self):
        result = []
        self._inorder(self.root, result)
        return result

    def _inorder(self, node, result):
        if node:
            self._inorder(node.left, result)
            result.append(node.value)
            self._inorder(node.right, result)

    def preorder(self):
        result = []
        self._preorder(self.root, result)
        return result

    def _preorder(self, node, result):
        if node:
            result.append(node.value)
            self._preorder(node.left, result)
            self._preorder(node.right, result)

    def postorder(self):
        result = []
        self._postorder(self.root, result)
        return result

    def _postorder(self, node, result):
        if node:
            self._postorder(node.left, result)
            self._postorder(node.right, result)
            result.append(node.value)

    # ── Min / Max ─────────────────────────────────────────────────
    def find_min(self):
        if self.root is None:
            return None
        return self._find_min(self.root).value

    def find_max(self):
        if self.root is None:
            return None
        node = self.root
        while node.right:
            node = node.right
        return node.value

    # ── Height ────────────────────────────────────────────────────
    def height(self):
        return self._height(self.root)

    def _height(self, node):
        if node is None:
            return -1
        return 1 + max(self._height(node.left), self._height(node.right))

    # ── Count ─────────────────────────────────────────────────────
    def count(self):
        return len(self.inorder())

    # ── Visual Print (ağac şeklinde) ──────────────────────────────
    def print_tree(self):
        if self.root is None:
            print(f"  {Colors.YELLOW}(Ağac boş){Colors.RESET}")
            return
        lines = []
        self._build_tree_lines(self.root, "", True, lines)
        for line in lines:
            print(line)

    def _build_tree_lines(self, node, prefix, is_tail, lines):
        if node is None:
            return

        connector = "└── " if is_tail else "├── "
        lines.append(
            f"{prefix}{connector}"
            f"{Colors.CYAN}{Colors.BOLD}[{node.value}]{Colors.RESET}"
        )

        new_prefix = prefix + ("    " if is_tail else "│   ")

        children = []
        if node.right:
            children.append((node.right, False))
        if node.left:
            children.append((node.left, True))

        for i, (child, is_last) in enumerate(children):
            self._build_tree_lines(child, new_prefix, is_last, lines)


# ─── UI Fonksiyonları ─────────────────────────────────────────────
def print_header(bst):
    clear()
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("  ╔═══════════════════════════════════════════╗")
    print("  ║   🌳  Binary Search Tree Visualizer  🌳   ║")
    print("  ╚═══════════════════════════════════════════╝")
    print(f"{Colors.RESET}")

    node_count = bst.count()
    height     = bst.height()
    min_val    = bst.find_min()
    max_val    = bst.find_max()

    print(f"  {Colors.YELLOW}━━━ Ağac Bilgileri ━━━{Colors.RESET}")
    print(f"  Node sayısı : {Colors.GREEN}{node_count}{Colors.RESET}")
    print(f"  Yükseklik   : {Colors.GREEN}{height}{Colors.RESET}")
    print(f"  Min değer   : {Colors.GREEN}{min_val}{Colors.RESET}")
    print(f"  Max değer   : {Colors.GREEN}{max_val}{Colors.RESET}")
    print()

def print_menu():
    print(f"  {Colors.YELLOW}━━━ Menü ━━━{Colors.RESET}")
    print(f"  {Colors.GREEN}1{Colors.RESET} → Insert (ekle)")
    print(f"  {Colors.GREEN}2{Colors.RESET} → Delete (sil)")
    print(f"  {Colors.GREEN}3{Colors.RESET} → Search (ara)")
    print(f"  {Colors.GREEN}4{Colors.RESET} → Traversals")
    print(f"  {Colors.GREEN}5{Colors.RESET} → Print Tree (ağacı göster)")
    print(f"  {Colors.GREEN}6{Colors.RESET} → Clear (temizle)")
    print(f"  {Colors.GREEN}0{Colors.RESET} → Çıkış")
    print()

def show_status(msg, color=Colors.GREEN):
    print(f"  {color}{Colors.BOLD}→ {msg}{Colors.RESET}\n")

def get_input(prompt):
    try:
        return int(input(f"  {Colors.CYAN}{prompt}{Colors.RESET} "))
    except ValueError:
        return None
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)


# ─── Ana Loop ─────────────────────────────────────────────────────
def main():
    bst = BST()

    # Başlangıç verileri
    for v in [50, 30, 70, 20, 40, 60, 80]:
        bst.insert(v)

    while True:
        print_header(bst)

        # Ağacı her iterasyonda göster
        print(f"  {Colors.YELLOW}━━━ Ağac ━━━{Colors.RESET}")
        bst.print_tree()
        print()

        print_menu()

        choice = get_input("Seç (0-6):")

        # ── 1: Insert ───────────────────────────────────────────
        if choice == 1:
            val = get_input("Ekleyeceğin sayı:")
            if val is None:
                show_status("Geçerli sayı gir!", Colors.RED)
            elif bst.insert(val):
                show_status(f"{val} eklendi ✓")
            else:
                show_status(f"{val} zaten var!", Colors.RED)
            input("  Devam için Enter...")

        # ── 2: Delete ───────────────────────────────────────────
        elif choice == 2:
            val = get_input("Sileyeceğin sayı:")
            if val is None:
                show_status("Geçerli sayı gir!", Colors.RED)
            elif bst.delete(val):
                show_status(f"{val} silindi ✓")
            else:
                show_status(f"{val} bulunamadı!", Colors.RED)
            input("  Devam için Enter...")

        # ── 3: Search ───────────────────────────────────────────
        elif choice == 3:
            val = get_input("Arayacağın sayı:")
            if val is None:
                show_status("Geçerli sayı gir!", Colors.RED)
            else:
                found, path = bst.search(val)
                path_str = " → ".join(str(x) for x in path)
                if found:
                    show_status(f"{val} bulundu ✓  |  Yol: {path_str}")
                else:
                    show_status(f"{val} bulunamadı ✗  |  Yol: {path_str}", Colors.RED)
            input("  Devam için Enter...")

        # ── 4: Traversals ───────────────────────────────────────
        elif choice == 4:
            print(f"  {Colors.YELLOW}━━━ Traversals ━━━{Colors.RESET}")
            print(f"  {Colors.CYAN}Inorder   :{Colors.RESET}  {bst.inorder()}")
            print(f"  {Colors.CYAN}Preorder  :{Colors.RESET}  {bst.preorder()}")
            print(f"  {Colors.CYAN}Postorder :{Colors.RESET}  {bst.postorder()}")
            print()
            input("  Devam için Enter...")

        # ── 5: Print Tree ───────────────────────────────────────
        elif choice == 5:
            input("  Devam için Enter...")  # zaten yukarıda gösteriliyor

        # ── 6: Clear ────────────────────────────────────────────
        elif choice == 6:
            bst = BST()
            show_status("Ağac temizlendi ✓")
            input("  Devam için Enter...")

        # ── 0: Çıkış ────────────────────────────────────────────
        elif choice == 0:
            print(f"\n  {Colors.GREEN}Görüşmek üzere! 👋{Colors.RESET}\n")
            break

        else:
            show_status("Geçerli bir seçenek yaz!", Colors.RED)
            input("  Devam için Enter...")


if __name__ == "__main__":
    main()
from mkdocs.structure.files import File, Files

class FileLinkedNode(object):
    """File linked list node class.

    Attributes:
        file: The file associated with this node.
        prev: The previous node in the linked list.
        next: The next node in the linked list.
    """
    def __init__(self, file: File):
        self.file = file
        self.prev: FileLinkedNode | None = None
        self.next: FileLinkedNode | None = None

    def insert(self, node: FileLinkedNode):
        """
        Insert the current node after the given node.
        """
        self.prev = node
        self.next = node.next
        if node.next:
            node.next.prev = self
        node.next = self

    def remove(self):
        """
        Remove the current node from the linked list.
        """
        if self.prev:
            self.prev.next = self.next
        if self.next:
            self.next.prev = self.prev

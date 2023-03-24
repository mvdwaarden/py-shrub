from typing import List


def list_block_iterator(the_list: List, blocksize: int):
    """Generic list block iterator
    Iteration will be over the list divided in blocksize blocks
    """
    result = []
    size = len(the_list)
    while size > 0:
        block = the_list[:blocksize]
        the_list = the_list[blocksize:]
        size -= len(block)
        result.append(block)
    return result

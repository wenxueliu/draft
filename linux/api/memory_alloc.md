

Whereas malloc gives you a chunk of memory that could have any alignment (the only requirement is that it must be aligned for the largest primitive type that the implementation supports), posix_memalign gives you a chunk of memory that is guaranteed to have the requested alignment.

So the result of e.g. posix_memalign(&p, 32, 128) will be a 128-byte chunk of memory whose start address is guaranteed to be a multiple of 32.

This is useful for various low-level operations (such as using SSE instructions, or DMA), that require memory that obeys a particular alignment.


The result of malloc does not have just "any" alignment. It is guaranteed to be suitably aligned for any native type on the system (int, long, double, structs, etc.). You are correct that larger alignments may be used for special purposes, but surely for the vast majority of applications, malloc's result is aligned just fine.


malloc always returns memory that is set to the maximum alignment required by any of the primitive types. This allows malloc'd memory to store any type you may need. My understanding of the description of posix_memalign, is that it returns a memory location who's address will be a multiple of whatever you specify as the alignment.

On recent x86 architectures a cache-line, which is the smallest amount of data that can fetched from memory to cache, is 64 bytes. Suppose your structure size is 56 bytes, you have a large array of them. When you lookup one element, the CPU will need to issue 2 memory requests (it might issue 2 requests even if it is in the middle of the cacheline). That is bad for performance, as you have to wait for memory, and you use more cache, which ultimately gives a higher cache-miss ratio. In this case it is not enough to just use posix_memalign, but you should pad or compact your structure to be on 64byte boundaries. 



Default malloc return pointer that are multiple of 8, It's mean malloc split memory to chunks have 8 bytes and check free memory at start of each chunk. There are 2 faces of problem.

Larger chunk will waste more memory, but larger chunk help C find free chunk memory faster. memalign can change how big those chunk is. If you want to save memory, decrease chunk's size to 2 or 4. If you want to make your application faster, increase chunk's size to power of 2.

	
###Is there a good reason to prefer posix_memalign over mmap, which allocates aligned memory?

posix_memalign will normally allocate a block from the heap, whereas mmap will always go to the operating system. If, for example, you wanted to allocate many cache line aligned blocks of memory, then posix_memalign is much preferred. It's the same reason to prefer malloc over mmap.





#include <stdlib.h>
#include <stdio.h>

void *malloc_aligned(size_t alignment, size_t bytes)
{
    // we need to allocate enough storage for the requested bytes, some 
    // book-keeping (to store the location returned by malloc) and some extra
    // padding to allow us to find an aligned byte.  im not entirely sure if 
    // 2 * alignment is enough here, its just a guess.
    const size_t total_size = bytes + (2 * alignment) + sizeof(size_t);

    // use malloc to allocate the memory.
    char *data = malloc(sizeof(char) * total_size);

    if (data)
    {
        // store the original start of the malloc'd data.
        const void * const data_start = data;

        // dedicate enough space to the book-keeping.
        data += sizeof(size_t);

        // find a memory location with correct alignment.  the alignment minus 
        // the remainder of this mod operation is how many bytes forward we need 
        // to move to find an aligned byte.
        const size_t offset = alignment - (((size_t)data) % alignment);

        // set data to the aligned memory.
        data += offset;

        // write the book-keeping.
        size_t *book_keeping = (size_t*)(data - sizeof(size_t));
        *book_keeping = (size_t)data_start;
    }

    return data;
}

void free_aligned(void *raw_data)
{
    if (raw_data)
    {
        char *data = raw_data;

        // we have to assume this memory was allocated with malloc_aligned.  
        // this means the sizeof(size_t) bytes before data are the book-keeping 
        // which points to the location we need to pass to free.
        data -= sizeof(size_t);

        // set data to the location stored in book-keeping.
        data = (char*)(*((size_t*)data));

        // free the memory.
        free(data);
    }
}

int main()
{
    char *ptr = malloc_aligned(7, 100);

    printf("is 5 byte aligned = %s\n", (((size_t)ptr) % 5) ? "no" : "yes");
    printf("is 7 byte aligned = %s\n", (((size_t)ptr) % 7) ? "no" : "yes");

    free_aligned(ptr);

    return 0;
}


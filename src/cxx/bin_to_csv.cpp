#include <cstdio>
#include <cstdint>
#include <cstdlib>

using std::FILE;

using std::exit;
using std::fopen;
using std::fread;
using std::fseek;
using std::ftell;
using std::rewind;

int main(int argc, char *argv[]) {
  if (argc != 2) {
    exit(-1);
  }
  
  FILE* fp = fopen(argv[1], "rb");
  if (!fp) {
    printf("Cannot open :");
    printf("%s", argv[0]);
    printf("\n");
    exit(-1);
  }
  fseek(fp, 0, SEEK_END);
  int size = ftell(fp);
  if (size == 0) {
    exit(0);
  }
  rewind(fp);

  for (int i = 0; i < size; i += 20) {
    char buf1[20];
    fread(buf1, 4, 5, fp);
    char buf2[20];
    for (int j = 0; j < 5; ++j) {
      buf2[j * 4 + 0] = buf1[j * 4  + 3];
      buf2[j * 4 + 1] = buf1[j * 4  + 2];
      buf2[j * 4 + 2] = buf1[j * 4  + 1];
      buf2[j * 4 + 3] = buf1[j * 4  + 0];
    }
    printf("%u,%u,%u,%.2f,%.2f\n", *(uint32_t *)(buf2 + 0), *(uint32_t *)(buf2 + 4), *(uint32_t *)(buf2 + 8), *(float *)(buf2 + 12), *(float *)(buf2 + 16));
  }
  fclose(fp);
}


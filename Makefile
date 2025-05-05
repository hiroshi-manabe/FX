# ---------  build settings  -----------------------------------------------
CXX       ?= g++
CXXFLAGS  ?= -std=c++17 -O2 -Wall -Wextra -I$(SRC_DIR)/cxx
LDFLAGS   ?=

# Detect shared‑library extension (Linux => .so, macOS => .dylib)
UNAME_S  := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    SHLIB_EXT := dylib
    SHARED    := -shared -dynamiclib
else
    SHLIB_EXT := so
    SHARED    := -shared -fPIC
endif

# ---------  project layout  ------------------------------------------------
SRC_DIR   := src
CXX_DIR   := $(SRC_DIR)/cxx
BUILD_DIR := build
BIN_DIR   := $(BUILD_DIR)/bin
LIB_DIR   := $(BUILD_DIR)/lib

# ---------  helper list  ---------------------------------------------------
# Map each executable to its single‑file source.

EXEC_MAP  := \
    bin_to_csv    = bin_to_csv.cpp       \
    label_pl      = label_pl.cpp     \
    fit_quadratic = fit_quadratic.cpp \
    filter_digest = filter_digest.cpp

# Shared libraries (name => source).  Currently only knn.
SHLIB_MAP := \
    libknn      = knn.cpp

# ---------  derived lists  -------------------------------------------------
EXECUTABLES := $(addprefix $(BIN_DIR)/, $(foreach p,$(EXEC_MAP),$(firstword $(subst =, ,$(p)))))
SHARED_LIBS := $(addprefix $(LIB_DIR)/, $(foreach p,$(SHLIB_MAP),$(firstword $(subst =, ,$(p))).$(SHLIB_EXT)))

# ---------  default target  ------------------------------------------------
.PHONY: all
all: $(EXECUTABLES) $(SHARED_LIBS)
	@echo "Build finished."

# ---------  rules for executables  ----------------------------------------
$(BIN_DIR)/%: $(CXX_DIR)/%.cpp | $(BIN_DIR)
	@echo "  [CXX] $@"
	$(CXX) $(CXXFLAGS) $< -o $@ $(LDFLAGS)

$(BIN_DIR):
	@mkdir -p $@

# ---------  rules for shared libraries  -----------------------------------
$(LIB_DIR)/%.$(SHLIB_EXT): $(CXX_DIR)/%.cpp $(CXX_DIR)/%.h | $(LIB_DIR)
	@echo "  [CXX] $@"
	$(CXX) $(CXXFLAGS) $(SHARED) $< -o $@ $(LDFLAGS)

$(LIB_DIR):
	@mkdir -p $@

# ---------  convenience targets  ------------------------------------------
.PHONY: clean
clean:
	@rm -rf $(BUILD_DIR)
	@echo "Cleaned."

.PHONY: rebuild
rebuild: clean all

# ---------  dependency mapping helpers  -----------------------------------
# Expand EXEC_MAP into explicit rules
$(foreach mapping,$(EXEC_MAP),\
  $(eval $(BIN_DIR)/$(firstword $(subst =, ,$(mapping))): $(CXX_DIR)/$(strip $(word 2,$(subst =, ,$(mapping))))) \
)

# Expand SHLIB_MAP rules
$(foreach mapping,$(SHLIB_MAP),\
  $(eval $(LIB_DIR)/$(firstword $(subst =, ,$(mapping))).$(SHLIB_EXT): $(CXX_DIR)/$(strip $(word 2,$(subst =, ,$(mapping))))) \
)

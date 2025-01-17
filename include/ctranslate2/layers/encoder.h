#pragma once

#include "ctranslate2/layers/common.h"
#include "ctranslate2/storage_view.h"

namespace ctranslate2 {
  namespace layers {

    // Base class for encoders.
    class Encoder : public Layer {
    public:
      virtual size_t num_input_features() const {
        return 1;
      }

      virtual void operator()(const std::vector<StorageView>& ids,
                              const StorageView& lengths,
                              StorageView& output) = 0;
    };

  }
}

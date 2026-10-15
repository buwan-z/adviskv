#pragma once

#include "catalog.pb.h"
#include "topo.pb.h"
#include "storage.pb.h"

namespace raftbox {

namespace catalog_rpc = ::raftbox::catalog::rpc;
namespace topo_rpc = ::raftbox::topo::rpc;
namespace storage_rpc = ::raftbox::rpc;

}  // namespace raftbox

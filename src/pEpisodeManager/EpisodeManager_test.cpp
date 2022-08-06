#include "EpisodeManager.h"
#include "MockMOOSCastingApp.h"
#include <gtest/gtest.h>

TEST(TestEpisodeManager, TestBasic) {
  EpisodeManager<MockMOOSCastingApp> mgr;

  mgr.PerformStartUp("pEpisodeManager", "/Users/carter/src/moos-ivp-agent/missions/AgentAquaticus/heron/plug_pEpisodeManager.moos");

  EXPECT_CALL(mgr, Register("IVPHELM_STATE"));
}
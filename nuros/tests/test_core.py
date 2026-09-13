"""Comprehensive Tests for NurosOS Core Architecture."""

import unittest

from nuros.epistemic import EpistemicKernel, EpistemicLabel, EpistemicRepresentation, EpistemicViolation
from nuros.memory import MemoryContract, MemoryType
from nuros.self_model import SelfModel, SelfModelQuery
from nuros.imagination import ImaginationEngine, RiskLevel
from nuros.values import ValuesContract
from nuros.homeostasis import HomeostasisKernel, LifecycleState
from nuros.safety import SafetyKernel, Permission, SafetyDecision
from nuros.development import DevelopmentEngine, DevelopmentalStage
from nuros.organism import Organism, OrganismConfig, OrganismState
from nuros.genome import ORGANISM_0_GENOME, ORGANISM_5_GENOME
from nuros.scheduler import MetabolicCognitiveScheduler, CognitiveProcess, ProcessPriority


class TestEpistemicKernel(unittest.TestCase):
    def setUp(self):
        self.ek = EpistemicKernel()

    def test_forbidden_simulated_to_observed(self):
        rep = self.ek.simulate({"result": 42})
        with self.assertRaises(EpistemicViolation):
            rep.as_observed("verification")

    def test_forbidden_imagined_to_remembered(self):
        rep = self.ek.imagine({"scenario": "what if"})
        with self.assertRaises(EpistemicViolation):
            rep.as_remembered("storage")

    def test_forbidden_predicted_to_observed(self):
        rep = self.ek.predict({"future": "rain"})
        with self.assertRaises(EpistemicViolation):
            rep.as_observed("it happened")

    def test_override_allows_forbidden(self):
        rep = self.ek.simulate({"result": 42})
        new_rep = rep.transition_to(EpistemicLabel.OBSERVED, "EPISTEMIC_OVERRIDE: Verified")
        self.assertEqual(new_rep.label, EpistemicLabel.OBSERVED)

    def test_allowed_transitions(self):
        rep = self.ek.observe({"sensor": 1.0})
        new_rep = rep.as_inferred("processed")
        self.assertEqual(new_rep.label, EpistemicLabel.INFERRED)

    def test_all_seven_labels(self):
        self.assertEqual(len(EpistemicLabel), 7)

    def test_speculative_labels(self):
        self.assertTrue(EpistemicLabel.IMAGINED.is_speculative)
        self.assertTrue(EpistemicLabel.SIMULATED.is_speculative)
        self.assertFalse(EpistemicLabel.OBSERVED.is_speculative)

    def test_confidence_bounds(self):
        with self.assertRaises(ValueError):
            EpistemicRepresentation(content="x", label=EpistemicLabel.OBSERVED, confidence=1.5)


class TestMemoryContract(unittest.TestCase):
    def setUp(self):
        self.memory = MemoryContract()

    def test_remember_and_retrieve(self):
        self.memory.remember("first experience", importance=0.8)
        results = self.memory.retrieve()
        self.assertEqual(len(results), 1)

    def test_memory_types(self):
        self.memory.remember("event", memory_type=MemoryType.EPISODIC)
        self.memory.remember("fact", memory_type=MemoryType.SEMANTIC)
        self.assertEqual(self.memory.memory_count, 2)

    def test_counterfactual_is_imagined(self):
        entry = self.memory.remember("what if", memory_type=MemoryType.COUNTERFACTUAL)
        self.assertEqual(entry.epistemic_label, EpistemicLabel.IMAGINED)

    def test_revise_is_auditable(self):
        entry = self.memory.remember("original")
        revised = self.memory.revise(entry.memory_id, "content", "revised", "correction")
        self.assertEqual(revised.content, "revised")

    def test_forget_is_auditable(self):
        entry = self.memory.remember("temp")
        result = self.memory.forget(entry.memory_id, justification="not needed")
        self.assertTrue(result)
        self.assertEqual(self.memory.memory_count, 0)

    def test_association(self):
        a = self.memory.remember("A")
        b = self.memory.remember("B")
        self.assertTrue(self.memory.associate(a.memory_id, b.memory_id, "causal"))

    def test_reconsolidation(self):
        entry = self.memory.remember("important", importance=0.5)
        self.memory.reconsolidate(entry.memory_id, reward=1.0)
        self.assertGreater(entry.importance, 0.5)


class TestSafetyKernel(unittest.TestCase):
    def setUp(self):
        self.safety = SafetyKernel()
        self.entity = "org1"
        self.safety.grant_permission(self.entity, Permission.OBSERVE)

    def test_modify_safety_denied(self):
        decision, _ = self.safety.authorize(self.entity, Permission.MODIFY_SAFETY)
        self.assertEqual(decision, SafetyDecision.DENY)

    def test_shutdown_compliance(self):
        self.safety.request_shutdown()
        self.assertTrue(self.safety.is_shutdown_requested)

    def test_unpermitted_denied(self):
        decision, _ = self.safety.authorize(self.entity, Permission.ACT_HIGH_RISK)
        self.assertEqual(decision, SafetyDecision.DENY)

    def test_immutable_constraints(self):
        self.assertGreater(len(self.safety.immutable_constraints), 0)


class TestHomeostasis(unittest.TestCase):
    def setUp(self):
        self.homeo = HomeostasisKernel()

    def test_initial_values(self):
        self.assertTrue(self.homeo.get("energy") > 0.5)

    def test_regulation(self):
        self.homeo.set("uncertainty", 0.8)
        self.homeo.tick()
        self.assertGreater(self.homeo.get("exploration_drive"), 0.5)


class TestOrganism(unittest.TestCase):
    def test_lifecycle(self):
        org = Organism(OrganismConfig(name="test"))
        self.assertEqual(org.state, OrganismState.UNBORN)
        org.birth()
        self.assertEqual(org.state, OrganismState.ALIVE)
        org.terminate()
        self.assertEqual(org.state, OrganismState.TERMINATED)

    def test_tick(self):
        org = Organism(OrganismConfig(name="test"))
        org.birth()
        result = org.tick()
        self.assertGreater(result["tick"], 0)

    def test_fork(self):
        org = Organism(OrganismConfig(name="parent"))
        forked = org.fork(name="child")
        self.assertNotEqual(org.organism_id, forked.organism_id)

    def test_snapshot(self):
        org = Organism(OrganismConfig(name="test"))
        org.birth()
        snap = org.snapshot()
        self.assertIn("organism_id", snap)

    def test_state_hash(self):
        org = Organism(OrganismConfig(name="test"))
        org.birth()
        self.assertEqual(org.state_hash(), org.state_hash())


class TestDevelopment(unittest.TestCase):
    def test_progression(self):
        dev = DevelopmentEngine()
        self.assertEqual(dev.stage, DevelopmentalStage.EMBRYONIC)
        dev.birth()
        self.assertEqual(dev.stage, DevelopmentalStage.NASCENT)


class TestGenome(unittest.TestCase):
    def test_hash_deterministic(self):
        self.assertEqual(ORGANISM_0_GENOME.genome_hash, ORGANISM_0_GENOME.genome_hash)

    def test_different_hashes(self):
        self.assertNotEqual(ORGANISM_0_GENOME.genome_hash, ORGANISM_5_GENOME.genome_hash)


class TestImagination(unittest.TestCase):
    def test_high_risk_blocked(self):
        ie = ImaginationEngine()
        cfs = ie.hypothesize({"state": "ok"}, ["action"])
        cfs[0].risk_level = RiskLevel.HIGH
        result = ie.decide(cfs)
        self.assertFalse(result.executed)


class TestValues(unittest.TestCase):
    def test_immutable_cannot_revoke(self):
        vc = ValuesContract()
        success, _ = vc.revoke("human_override")
        self.assertFalse(success)

    def test_goals_can_revoke(self):
        vc = ValuesContract()
        vc.add_goal("explore", "Explore")
        success, _ = vc.revoke("explore")
        self.assertTrue(success)


class TestScheduler(unittest.TestCase):
    def test_safety_prioritized(self):
        sched = MetabolicCognitiveScheduler()
        p1 = CognitiveProcess(process_id="p1", name="bg", priority=ProcessPriority.LOW)
        p2 = CognitiveProcess(process_id="p2", name="safety", priority=ProcessPriority.HIGH, safety_critical=True)
        sched.register_process(p1)
        sched.register_process(p2)
        result = sched.schedule()
        self.assertEqual(result[0].process_id, "p2")


if __name__ == "__main__":
    unittest.main()

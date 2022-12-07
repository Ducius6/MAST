from unittest import TestCase
from MastExceptions import RootNotReachable, NodeNotValid, LeafNodeNotValid, RootNodeHashDoesNotMatch
import pytest

from MAST import MASTBuilder
from MAST import MASTVerification

global_state = {'time_in_millis': '123', 'current_block': '256'}


class TestMast(TestCase):

    def test_correct_execution_1(self):
        text = '{time_in_millis < 450} + {time_in_millis < 560} * ({current_block == 256} + {time_in_millis >= 4})'

        # Create MAST structure and generate root hash and evidence list
        mast_builder = MASTBuilder(text)
        root_hash, evidence_list = mast_builder.create_mast_object()

        # Verify evidence scripts and its part of upward verify root hash
        mast_verificator1 = MASTVerification(root_hash, global_state,
                                             [evidence_list[1], evidence_list[3]])
        mast_verificator2 = MASTVerification(root_hash, global_state,
                                             [evidence_list[1], evidence_list[2]])
        mast_verificator3 = MASTVerification(root_hash, global_state,
                                             [evidence_list[0]])

        self.assertTrue(mast_verificator1.verify_mast())
        self.assertTrue(mast_verificator2.verify_mast())
        self.assertTrue(mast_verificator3.verify_mast())

    def test_correct_execution_2(self):
        text = '(({time_in_millis < 450}) + ({time_in_millis < 560} * {current_block >= 10})) * ({current_block == 256} + {time_in_millis >= 4})'

        # Create MAST structure and generate root hash and evidence list
        mast_builder = MASTBuilder(text)
        root_hash, evidence_list = mast_builder.create_mast_object()

        # Verify evidence scripts and its part of upward verify root hash
        mast_verificator1 = MASTVerification(root_hash, global_state,
                                             [evidence_list[0], evidence_list[3]])
        mast_verificator2 = MASTVerification(root_hash, global_state,
                                             [evidence_list[1], evidence_list[2], evidence_list[4]])

        self.assertTrue(mast_verificator1.verify_mast())
        self.assertTrue(mast_verificator2.verify_mast())

    def test_not_enough_evidence_to_reach_root(self):
        text = '(({time_in_millis < 450}) + ({time_in_millis < 560} * {current_block >= 10})) * ({current_block == 256} + {time_in_millis >= 4})'

        # Create MAST structure and generate root hash and evidence list
        mast_builder = MASTBuilder(text)
        root_hash, evidence_list = mast_builder.create_mast_object()

        # Verify evidence scripts and its part of upward verify root hash
        mast_verificator1 = MASTVerification(root_hash, global_state,
                                             [evidence_list[0], evidence_list[1], evidence_list[2]])
        mast_verificator2 = MASTVerification(root_hash, global_state,
                                             [evidence_list[2], evidence_list[3], evidence_list[4]])

        with pytest.raises(RootNotReachable) as ex:
            mast_verificator1.verify_mast()
        with pytest.raises(RootNotReachable) as ex:
            mast_verificator2.verify_mast()

    def test_script_eval_fails(self):
        text = '{current_block == 56} + {time_in_millis >= 4543} + {current_block < 1000}'

        # Create MAST structure and generate root hash and evidence list
        mast_builder = MASTBuilder(text)
        root_hash, evidence_list = mast_builder.create_mast_object()

        # Verify evidence scripts and its part of upward verify root hash

        mast_verificator1 = MASTVerification(root_hash, global_state,
                                             [evidence_list[0]])
        mast_verificator2 = MASTVerification(root_hash, global_state,
                                             [evidence_list[1]])
        mast_verificator3 = MASTVerification(root_hash, global_state,
                                             [evidence_list[2]])

        self.assertTrue(mast_verificator3.verify_mast())
        with pytest.raises(LeafNodeNotValid) as ex:
            mast_verificator1.verify_mast()

        with pytest.raises(LeafNodeNotValid) as ex:
            mast_verificator2.verify_mast()

    def test_courrupted_evidence_hash(self):
        text = '{current_block == 256} + {time_in_millis >= 4}'

        # Create MAST structure and generate root hash and evidence list
        mast_builder = MASTBuilder(text)
        root_hash, evidence_list = mast_builder.create_mast_object()

        # Verify evidence scripts and its part of upward verify root hash
        evidence = evidence_list[0]
        evidence.hash_value += 'a'
        mast_verificator1 = MASTVerification(root_hash, global_state,
                                             [evidence])

        with pytest.raises(LeafNodeNotValid) as ex:
            mast_verificator1.verify_mast()

    def test_incorrect_root_hash(self):
        text = '{current_block == 256} + {time_in_millis >= 4}'

        # Create MAST structure and generate root hash and evidence list
        mast_builder = MASTBuilder(text)
        root_hash, evidence_list = mast_builder.create_mast_object()

        # Verify evidence scripts and its part of upward verify root hash

        mast_verificator1 = MASTVerification(root_hash + 'a', global_state,
                                             [evidence_list[0]])
        mast_verificator2 = MASTVerification(root_hash, global_state,
                                             [evidence_list[0]])

        self.assertTrue(mast_verificator2.verify_mast())
        with pytest.raises(RootNodeHashDoesNotMatch) as ex:
            mast_verificator1.verify_mast()

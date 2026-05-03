package com.tianqingyuluo.waterapproval.common;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import static org.junit.jupiter.api.Assertions.*;

class ProcessingStatusTest {

    @Test
    void shouldAcceptValidStatusValues() {
        assertTrue(ProcessingStatus.isValid("SUBMITTED"));
        assertTrue(ProcessingStatus.isValid("QUEUED"));
        assertTrue(ProcessingStatus.isValid("PROCESSING"));
        assertTrue(ProcessingStatus.isValid("PARTIAL_SUCCESS"));
        assertTrue(ProcessingStatus.isValid("COMPLETED"));
        assertTrue(ProcessingStatus.isValid("FAILED"));
    }

    @Test
    void shouldRejectInvalidStatusValues() {
        assertFalse(ProcessingStatus.isValid("INVALID"));
        assertFalse(ProcessingStatus.isValid(""));
        assertFalse(ProcessingStatus.isValid(null));
        assertFalse(ProcessingStatus.isValid("CANCELLED"));
    }

    @ParameterizedTest
    @CsvSource({
            "SUBMITTED, QUEUED",
            "SUBMITTED, PROCESSING",
            "SUBMITTED, FAILED",
            "QUEUED, PROCESSING",
            "QUEUED, FAILED",
            "PROCESSING, COMPLETED",
            "PROCESSING, PARTIAL_SUCCESS",
            "PROCESSING, FAILED",
    })
    void shouldAllowValidTransitions(String from, String to) {
        assertDoesNotThrow(() -> ProcessingStatus.validateTransition(from, to));
    }

    @ParameterizedTest
    @CsvSource({
            "SUBMITTED, COMPLETED",
            "SUBMITTED, PARTIAL_SUCCESS",
            "QUEUED, COMPLETED",
            "QUEUED, PARTIAL_SUCCESS",
            "QUEUED, SUBMITTED",
            "PROCESSING, SUBMITTED",
            "PROCESSING, QUEUED",
            "COMPLETED, PROCESSING",
            "COMPLETED, FAILED",
            "PARTIAL_SUCCESS, PROCESSING",
            "PARTIAL_SUCCESS, FAILED",
            "FAILED, PROCESSING",
            "FAILED, COMPLETED",
            "FAILED, PARTIAL_SUCCESS",
    })
    void shouldRejectInvalidTransitions(String from, String to) {
        assertThrows(IllegalArgumentException.class,
                () -> ProcessingStatus.validateTransition(from, to));
    }

    @Test
    void shouldAllowSameStateTransition() {
        assertDoesNotThrow(() -> ProcessingStatus.validateTransition("PROCESSING", "PROCESSING"));
        assertDoesNotThrow(() -> ProcessingStatus.validateTransition("COMPLETED", "COMPLETED"));
    }

    @Test
    void shouldRejectTransitionFromInvalidCurrentState() {
        assertThrows(IllegalArgumentException.class,
                () -> ProcessingStatus.validateTransition("INVALID", "PROCESSING"));
    }

    @Test
    void shouldRejectTransitionToInvalidState() {
        assertThrows(IllegalArgumentException.class,
                () -> ProcessingStatus.validateTransition("SUBMITTED", "INVALID"));
    }

    @Test
    void shouldIdentifyTerminalStates() {
        assertFalse(ProcessingStatus.isTerminal("SUBMITTED"));
        assertFalse(ProcessingStatus.isTerminal("QUEUED"));
        assertFalse(ProcessingStatus.isTerminal("PROCESSING"));
        assertTrue(ProcessingStatus.isTerminal("PARTIAL_SUCCESS"));
        assertTrue(ProcessingStatus.isTerminal("COMPLETED"));
        assertTrue(ProcessingStatus.isTerminal("FAILED"));
    }
}

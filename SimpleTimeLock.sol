// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SimpleTimeLock {
    address public depositor;
    uint public unlockTime;
    uint public lockedAmount;

    // Event to log successful withdrawal
    event FundsWithdrawn(address indexed _to, uint _amount);

    constructor(uint _lockDurationSeconds) payable {
        require(_lockDurationSeconds > 0, "Lock duration must be greater than 0");
        require(msg.value > 0, "Must deposit Ether to lock");

        depositor = msg.sender;
        unlockTime = block.timestamp + _lockDurationSeconds;
        lockedAmount = msg.value;
    }

    // Function to allow the depositor to withdraw funds after the unlock time
    function withdraw() public {
        require(msg.sender == depositor, "Only the depositor can withdraw");
        require(block.timestamp >= unlockTime, "Funds are still locked");
        require(lockedAmount > 0, "No locked funds to withdraw");

        uint amountToWithdraw = lockedAmount;
        lockedAmount = 0; // Prevent re-entry and ensure funds are not double-withdrawn

        // Transfer the funds back to the depositor
        (bool success, ) = payable(depositor).call{value: amountToWithdraw}("");
        require(success, "Failed to withdraw Ether");

        emit FundsWithdrawn(depositor, amountToWithdraw);
    }

    // Fallback function to receive Ether if sent directly
    receive() external payable {
        revert("Direct Ether deposits not allowed after deployment. Use constructor.");
    }
}
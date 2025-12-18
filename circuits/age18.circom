pragma circom 2.1.6;

template Age18() {
    signal input birthYear;     // PRIVATE
    signal input currentYear;   // PUBLIC (we will expose this as public signal)
    signal output ok;

    // Compute age
    signal age;
    age <== currentYear - birthYear;

    // Enforce age >= 18
    age >= 18;

    ok <== 1;
}

component main { public [currentYear] } = Age18();

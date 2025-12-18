
pragma circom 2.1.6;

template Age18() {
    signal input birthYear;     // PRIVATE
    signal input currentYear;   // PUBLIC
    signal output ok;

    signal age;
    age <== currentYear - birthYear;

    age >= 18;

    ok <== 1;
}

component main { public [currentYear] } = Age18();

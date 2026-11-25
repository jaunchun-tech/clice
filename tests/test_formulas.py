"""Unit tests for Clice Sheets formula engine."""

from clice.core.formulas import col_letters_to_index, evaluate_cell, index_to_col_letters


def test_column_letter_conversions():
    assert col_letters_to_index("A") == 0
    assert col_letters_to_index("Z") == 25
    assert col_letters_to_index("AA") == 26
    assert index_to_col_letters(0) == "A"
    assert index_to_col_letters(25) == "Z"
    assert index_to_col_letters(26) == "AA"


def test_basic_arithmetic_and_cell_refs():
    grid = [
        ["10", "20", "=A1+B1"],
        ["5", "2", "=A2^B2"],
    ]
    assert evaluate_cell(grid[0][2], grid) == "30"
    assert evaluate_cell(grid[1][2], grid) == "25"


def test_ranges_and_functions():
    grid = [
        ["10", "20"],
        ["30", "40"],
        ["=SUM(A1:B2)", "=AVG(A1:B2)"],
        ["=MIN(A1:B2)", "=MAX(A1:B2)"],
        ["=COUNT(A1:B2)", "=IF(A3>50,'BIG','SMALL')"],
    ]
    assert evaluate_cell(grid[2][0], grid) == "100"
    assert evaluate_cell(grid[2][1], grid) == "25"
    assert evaluate_cell(grid[3][0], grid) == "10"
    assert evaluate_cell(grid[3][1], grid) == "40"
    assert evaluate_cell(grid[4][0], grid) == "4"
    assert evaluate_cell(grid[4][1], grid) == "BIG"


def test_error_handling():
    grid = [["=1/0", "=A1", "=B1"]]
    assert evaluate_cell(grid[0][0], grid) == "#DIV/0!"
    circ = [["=B1", "=A1"]]
    assert evaluate_cell(circ[0][0], circ) == "#ERR!"

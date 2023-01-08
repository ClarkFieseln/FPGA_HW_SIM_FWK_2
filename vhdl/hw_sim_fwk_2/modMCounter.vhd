-- Code (adapted) from:
-- https://vhdlguide.readthedocs.io/en/latest/vhdl/vvd.html#ch-visualverification
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;


entity modMCounter is
    generic(
        M : integer := 5; -- count from 0 to M-1
        N : integer := 3  -- N bits required to count upto M i.e. 2**N >= M
    );
    port(
        clock, reset  : in  std_logic;
        complete_tick : out std_logic;
        count         : out std_logic_vector(N - 1 downto 0)
    );
end modMCounter;

architecture arch of modMCounter is
    signal count_reg, count_next : unsigned(N - 1 downto 0);
begin
    -- process counter
    -- ###############
    proc_counter : process(clock, reset, count_reg)
    begin
        if reset = '1' then
            count_reg <= (others => '0');
        elsif rising_edge(clock) then
            count_reg <= count_next;
        else -- NOTE: else block is not required
            count_reg <= count_reg;
        end if;
    end process proc_counter;
    -- output signals
    -- ##############
    -- set count_next to 0 when maximum count is reached i.e. (M-1)
    -- otherwise increase the count
    count_next    <= (others => '0') when count_reg = (M - 1) else (count_reg + 1);
    -- Generate 'tick' on each maximum count
    complete_tick <= '1' when count_reg = (M - 1) else '0';
    -- assign value to output port
    count         <= std_logic_vector(count_reg);
end arch;


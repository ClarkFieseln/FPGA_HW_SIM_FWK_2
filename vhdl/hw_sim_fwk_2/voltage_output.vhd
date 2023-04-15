library ieee;
use ieee.std_logic_1164.ALL;
use ieee.numeric_std.all;

entity voltage_output is
    generic(
        NR_VO_BITS : integer := 10;
        NR_BUTTONS  : integer := 2
    );
    port(
        reset  : in  std_logic;
        clock  : in  std_logic;
        button : in  std_logic_vector(NR_BUTTONS - 1 downto 0);
        vo     : out std_logic_vector(NR_VO_BITS - 1 downto 0)
    );
end voltage_output;

architecture Behavioral of voltage_output is
    signal vo_reg : std_logic_vector(NR_VO_BITS - 1 downto 0);
begin
    -- process buttons to set the voltage output frequency
    -- ###################################################
    proc_voltage_output : process(reset, clock)
    begin
        -- asynchronous reset 
        if (reset = '1') then
            vo_reg <= (others => '0');
        -- synchronous events
        elsif rising_edge(clock) then
            -- set lower LEDs by "oring" buttons and switches
            if button(0) = '1' then
				vo_reg(NR_VO_BITS-1 downto 0) <= std_logic_vector(to_unsigned(27, NR_VO_BITS));
			else
				vo_reg(NR_VO_BITS-1 downto 0) <= std_logic_vector(to_unsigned(32, NR_VO_BITS));
			end if;
        end if;
    end process proc_voltage_output;
    -- output signals
    -- ##############
    vo <= vo_reg;
end Behavioral;

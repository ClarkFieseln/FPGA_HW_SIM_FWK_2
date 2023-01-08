library ieee;
use ieee.std_logic_1164.ALL;


entity dio is
    generic(
        NR_DIS : integer := 2;
        NR_DOS : integer := 2
    );
    port(
        reset  : in  std_logic;
        clock  : in  std_logic;
        di     : in  std_logic_vector(NR_DIS - 1 downto 0);        
        do     : out std_logic_vector(NR_DOS - 1 downto 0)
    );
end dio;

architecture Behavioral of dio is
    -- Set USE_PROCESS_LOGIC to use process logic or just wire-through
    -- With wire-through we avoid using an additional register which also adds a new delay.
    -- But in case some additional logic is needed we do need this additional intermediate step.
    constant USE_PROCESS_LOGIC : boolean := false;
    signal do_reg : std_logic_vector(NR_DOS - 1 downto 0);
begin
    g_conditional_process : if USE_PROCESS_LOGIC = true generate
        -- process DIs, DOs
        -- ################
        -- NOTE: the di signal is "partially" inside the sensitivity list so we support "asynchronous" DIs for the "upper" DIs
        proc_dio : process(reset, clock, di(NR_DIS - 1 downto NR_DIS/2))
        begin
            -- asynchronous reset 
            if reset = '1' then
                do_reg <= (others => '0');
            -- synchronous events
            elsif rising_edge(clock) then
                do_reg <= di; 
            -- asynchronous DIs that might as well be output as asynchronous DOs
            elsif rising_edge(di(NR_DIS - 1)) then
                do_reg(NR_DIS - 1) <= di(NR_DIS - 1); 
            elsif rising_edge(di(NR_DIS - 2)) then
                do_reg(NR_DIS - 2) <= di(NR_DIS - 2); 
            elsif rising_edge(di(NR_DIS - 3)) then
                do_reg(NR_DIS - 3) <= di(NR_DIS - 3); 
            elsif rising_edge(di(NR_DIS - 4)) then
                do_reg(NR_DIS - 4) <= di(NR_DIS - 4);     
            elsif rising_edge(di(NR_DIS - 5)) then
                do_reg(NR_DIS - 5) <= di(NR_DIS - 5);                              
            end if;
        end process proc_dio;
        -- output signals
        -- ##############
        do <= do_reg;
    end generate g_conditional_process;
    -- Note: the "else generate" construct is only supported in VHDL 1076-2008
    --       so we use a separate (and complementary) generate condition
    g_conditional_wirethrough : if USE_PROCESS_LOGIC = false generate
        do <= di;
    end generate g_conditional_wirethrough;
end Behavioral;

